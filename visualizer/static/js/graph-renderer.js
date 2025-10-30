// 그래프 렌더링 및 시각화 모듈
export class GraphRenderer {
    constructor(containerId, width, height) {
        this.svg = d3.select(`#${containerId}`);
        this.width = width;
        this.height = height;
        this.simulation = null;
        this.nodeElements = null;
        this.linkElements = null;
        this.container = null;

        this.setupSVG();
    }

    setupSVG() {
        this.svg.attr("width", this.width).attr("height", this.height);

        this.zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", (event) => {
                this.container.attr("transform", event.transform);
            });

        this.svg.call(this.zoom);
        this.container = this.svg.append("g");
    }

    render(graphData, callbacks) {
        this.simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(120))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("center", d3.forceCenter(this.width / 2, this.height / 2))
            .force("collision", d3.forceCollide().radius(d => d.size + 5));

        this.container.selectAll("*").remove();

        this.linkElements = this.container.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(graphData.links)
            .enter().append("line")
            .attr("class", "link");

        this.nodeElements = this.container.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(graphData.nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("data-id", d => d.id)
            .attr("r", d => d.size)
            .attr("fill", d => d.color)
            .on("click", (event, d) => {
                event.stopPropagation();
                if (callbacks.onNodeClick) callbacks.onNodeClick(event, d);
            })
            .on("mouseover", (event, d) => {
                if (callbacks.onNodeMouseover) callbacks.onNodeMouseover(event, d);
            })
            .on("mouseout", () => {
                if (callbacks.onNodeMouseout) callbacks.onNodeMouseout();
            })
            .call(d3.drag()
                .on("start", (event, d) => this.dragStarted(event, d))
                .on("drag", (event, d) => this.dragged(event, d))
                .on("end", (event, d) => this.dragEnded(event, d)));

        const label = this.container.append("g")
            .attr("class", "labels")
            .selectAll("text")
            .data(graphData.nodes)
            .enter().append("text")
            .attr("class", "node-label")
            .attr("dy", 4)
            .text(d => d.name);

        this.simulation.on("tick", () => {
            this.linkElements
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            this.nodeElements
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        });
    }

    dragStarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragEnded(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    highlightNodesMultiHop(selectedNodeId, maxHops) {
        if (!this.nodeElements || !this.linkElements) {
            console.error('nodeElements or linkElements not initialized');
            return;
        }

        // 선택된 노드로 화면 중심 이동
        this.centerOnNode(selectedNodeId);

        const hopGroups = new Map();
        hopGroups.set(0, new Set([selectedNodeId]));

        for (let hop = 1; hop <= maxHops; hop++) {
            const currentHopNodes = new Set();
            const previousHopNodes = hopGroups.get(hop - 1);

            this.linkElements.each(function(d) {
                const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                const targetId = typeof d.target === 'object' ? d.target.id : d.target;

                if (previousHopNodes.has(sourceId) && !isNodeInAnyPreviousHop(targetId, hopGroups, hop - 1)) {
                    currentHopNodes.add(targetId);
                }
                if (previousHopNodes.has(targetId) && !isNodeInAnyPreviousHop(sourceId, hopGroups, hop - 1)) {
                    currentHopNodes.add(sourceId);
                }
            });

            hopGroups.set(hop, currentHopNodes);
        }

        this.clearAllHighlights();

        this.nodeElements.each(function(d) {
            const element = d3.select(this);
            if (d.id === selectedNodeId) {
                element.classed('highlighted', true);
            } else {
                for (let hop = 1; hop <= Math.min(maxHops, 5); hop++) {
                    if (hopGroups.get(hop).has(d.id)) {
                        element.classed(`hop-${hop}`, true);
                        break;
                    }
                }
                if (!isNodeInAnyHop(d.id, hopGroups, maxHops)) {
                    element.classed('dimmed', true);
                }
            }
        });

        this.linkElements.each(function(d) {
            const element = d3.select(this);
            const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
            const targetId = typeof d.target === 'object' ? d.target.id : d.target;

            let shouldHighlight = false;

            if (sourceId === selectedNodeId || targetId === selectedNodeId) {
                shouldHighlight = true;
            } else {
                const sourceInHop = isNodeInAnyHop(sourceId, hopGroups, maxHops);
                const targetInHop = isNodeInAnyHop(targetId, hopGroups, maxHops);

                if (sourceInHop && targetInHop) {
                    shouldHighlight = true;
                }
            }

            if (shouldHighlight) {
                element.classed('highlighted', true);
            } else {
                element.classed('dimmed', true);
            }
        });
    }

    clearAllHighlights() {
        if (this.nodeElements) {
            this.nodeElements
                .classed("highlighted", false)
                .classed("hop-1", false)
                .classed("hop-2", false)
                .classed("hop-3", false)
                .classed("hop-4", false)
                .classed("hop-5", false)
                .classed("dimmed", false);
        }

        if (this.linkElements) {
            this.linkElements
                .classed("highlighted", false)
                .classed("dimmed", false);
        }
    }

    applyFilters(iterationFilter, connectionFilter) {
        if (!this.nodeElements || !this.linkElements) return;

        this.nodeElements.each(function(d) {
            const element = d3.select(this);
            let shouldShow = true;

            if (iterationFilter !== null) {
                const createdAt = d.data.created_at;
                if (createdAt !== iterationFilter) {
                    shouldShow = false;
                }
            }

            if (connectionFilter !== null) {
                const connectionCount = Math.round(d.size / 3 - 3);
                if (connectionCount < connectionFilter) {
                    shouldShow = false;
                }
            }

            element.classed('filtered-out', !shouldShow);
        });

        this.linkElements.each(function(d) {
            const element = d3.select(this);
            const sourceNode = d3.select(`circle[data-id="${typeof d.source === 'object' ? d.source.id : d.source}"]`);
            const targetNode = d3.select(`circle[data-id="${typeof d.target === 'object' ? d.target.id : d.target}"]`);

            const sourceFiltered = sourceNode.classed('filtered-out');
            const targetFiltered = targetNode.classed('filtered-out');

            element.classed('filtered-out', sourceFiltered || targetFiltered);
        });
    }

    resize(newWidth, newHeight) {
        this.width = newWidth;
        this.height = newHeight;
        this.svg.attr("width", newWidth).attr("height", newHeight);

        if (this.simulation) {
            this.simulation.force("center", d3.forceCenter(newWidth / 2, newHeight / 2));
            this.simulation.alpha(0.3).restart();
        }
    }

    onBackgroundClick(callback) {
        this.svg.on("click", (event) => {
            if (event.target === this.svg.node()) {
                callback();
            }
        });
    }

    centerOnNode(nodeId) {
        // 노드 데이터 찾기
        const nodeData = this.nodeElements.data().find(d => d.id === nodeId);
        if (!nodeData) {
            console.error(`Node ${nodeId} not found`);
            return;
        }

        // SVG의 현재 transform 가져오기
        const currentTransform = d3.zoomTransform(this.svg.node());

        // 노드의 현재 위치
        const x = nodeData.x;
        const y = nodeData.y;

        // SVG 중앙 좌표
        const centerX = this.width / 2;
        const centerY = this.height / 2;

        // 새로운 transform 계산 (현재 줌 레벨 유지)
        const scale = currentTransform.k;
        const newX = centerX - x * scale;
        const newY = centerY - y * scale;

        // 애니메이션과 함께 이동
        this.svg.transition()
            .duration(750)
            .call(this.zoom.transform, d3.zoomIdentity.translate(newX, newY).scale(scale));
    }
}

// Helper functions
function isNodeInAnyPreviousHop(nodeId, hopGroups, currentHop) {
    for (let hop = 0; hop < currentHop; hop++) {
        if (hopGroups.get(hop).has(nodeId)) {
            return true;
        }
    }
    return false;
}

function isNodeInAnyHop(nodeId, hopGroups, maxHops) {
    for (let hop = 0; hop <= maxHops; hop++) {
        if (hopGroups.get(hop) && hopGroups.get(hop).has(nodeId)) {
            return true;
        }
    }
    return false;
}
