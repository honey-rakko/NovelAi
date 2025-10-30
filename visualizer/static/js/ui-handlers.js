// UI 이벤트 핸들러 및 DOM 조작 모듈
import { API } from './api.js';

export class UIHandlers {
    constructor(graphData) {
        this.graphData = graphData;
        this.tooltip = d3.select("#tooltip");
    }

    updateGraphData(graphData) {
        this.graphData = graphData;
    }

    // 툴팁 핸들러
    handleNodeMouseover(event, d) {
        this.tooltip
            .style("opacity", 1)
            .html(`
                <strong>${d.name}</strong><br>
                Type: ${d.type}<br>
                Connections: ${Math.round(d.size / 3 - 3)}
            `)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 10) + "px");
    }

    handleNodeMouseout() {
        this.tooltip.style("opacity", 0);
    }

    // 노드 상세 정보 표시
    async displayNodeDetails(nodeId) {
        try {
            const nodeData = await API.getNodeDetails(nodeId);
            const infoPanel = d3.select("#node-info");
            infoPanel.html("");

            let title = nodeData.data.name || nodeData.id;
            if (nodeData.type === "placeholder") {
                title = `[PlaceHolder] ${nodeData.data.role || 'Unknown'}`;
            } else if (nodeData.type === "info") {
                title = `[Info] ${nodeData.data.type || 'Unknown'}`;
            }

            infoPanel.append("h2").text(title);
            infoPanel.append("p").html(`<strong>ID:</strong> ${nodeData.id}`);
            infoPanel.append("p").html(`<strong>Type:</strong> ${nodeData.type}`);
            infoPanel.append("p").html(`<strong>Connections:</strong> ${nodeData.connections}`);
            infoPanel.append("p").html(`<strong>Created at:</strong> ${nodeData.data.created_at}`);

            this._displayTypeSpecificInfo(infoPanel, nodeData);
            this._displayConnectedNodes(infoPanel, nodeData.connected_nodes);

        } catch (error) {
            console.error("Error loading node details:", error);
        }
    }

    _displayTypeSpecificInfo(infoPanel, nodeData) {
        if (nodeData.type === "character") {
            if (nodeData.data.role) {
                infoPanel.append("p").html(`<strong>Role:</strong> ${nodeData.data.role}`);
            }

            if (nodeData.infos && nodeData.infos.length > 0) {
                infoPanel.append("h3").text("Related Information");
                const infoList = infoPanel.append("div").attr("class", "info-list");
                nodeData.infos.forEach(info => {
                    infoList.append("div")
                        .attr("class", "info-item")
                        .html(`<strong>${info.type}:</strong> ${info.content}`);
                });
            }
        } else if (nodeData.type === "event") {
            infoPanel.append("p").html(`<strong>Owner id:</strong> ${nodeData.data.owner_id}`);
            if (nodeData.data.summary) {
                infoPanel.append("h3").text("Summary");
                infoPanel.append("p").text(nodeData.data.summary);
            }

            if (nodeData.participants) {
                if (nodeData.participants.infos && nodeData.participants.infos.length > 0) {
                    infoPanel.append("h3").text("Info Nodes");
                    const infosList = infoPanel.append("ul");
                    nodeData.participants.infos.forEach(infoId => {
                        infosList.append("li").text(infoId);
                    });
                }

                if (nodeData.participants.placeholders && nodeData.participants.placeholders.length > 0) {
                    infoPanel.append("h3").text("PlaceHolders");
                    const phList = infoPanel.append("ul");
                    nodeData.participants.placeholders.forEach(phId => {
                        phList.append("li").text(phId);
                    });
                }
            }
        } else if (nodeData.type === "info") {
            infoPanel.append("p").html(`<strong>Info Type:</strong> ${nodeData.data.type || 'Unknown'}`);
            infoPanel.append("p").html(`<strong>Owner id:</strong> ${nodeData.data.owner_id}`);
            if (nodeData.data.content) {
                infoPanel.append("h3").text("Content");
                infoPanel.append("p").text(nodeData.data.content);
            }
        } else if (nodeData.type === "placeholder") {
            infoPanel.append("p").html(`<strong>Role:</strong> ${nodeData.data.role || 'Unknown'}`);
            infoPanel.append("p").html(`<strong>Owner id:</strong> ${nodeData.data.owner_id}`);
            if (nodeData.data.context) {
                infoPanel.append("h3").text("Context");
                infoPanel.append("p").text(nodeData.data.context);
            }
        }
    }

    _displayConnectedNodes(infoPanel, connectedNodeIds) {
        if (connectedNodeIds.length > 0) {
            infoPanel.append("h3").text("Connected Nodes");
            const connectedList = infoPanel.append("ul");
            connectedNodeIds.forEach(connectedId => {
                const connectedNode = this.graphData.nodes.find(n => n.id === connectedId);
                if (connectedNode) {
                    const listItem = connectedList.append("li");
                    listItem.append("span")
                        .attr("class", "connected-node")
                        .text(`${connectedNode.name} (${connectedNode.type})`)
                        .on("click", () => {
                            window.selectNodeFromSearch(connectedId);
                        });
                }
            });
        }
    }

    // 통계 표시
    async displayStatistics() {
        try {
            const stats = await API.getStatistics();
            const tableBody = d3.select("#stats-table");
            tableBody.selectAll("*").remove();

            const basicStats = [
                ["Total Nodes", stats.total_nodes],
                ["Total Edges", stats.total_edges],
                ["Characters", stats.characters || 0],
                ["Events", stats.events || 0],
                ["Info Nodes", stats.infos || 0],
                ["PlaceHolders", stats.placeholders || 0]
            ];

            basicStats.forEach(([key, value]) => {
                const row = tableBody.append("tr");
                row.append("th").text(key);
                row.append("td").text(value);
            });

        } catch (error) {
            console.error("Error loading statistics:", error);
        }
    }

    // 현재 파일 정보 표시
    displayFileInfo(metadata, topic) {
        if (metadata) {
            document.getElementById('current-file-info').style.display = 'block';
            document.getElementById('current-filename').textContent = metadata.filename || 'Unknown';
            document.getElementById('current-topic').textContent = topic || 'Unknown';
        }
        document.title = `CharacterNetwork: ${topic}`;
    }
}
