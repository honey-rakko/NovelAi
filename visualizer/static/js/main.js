// 메인 진입점 - 모든 모듈을 조합하여 애플리케이션 실행
import { API } from './api.js';
import { GraphRenderer } from './graph-renderer.js';
import { UIHandlers } from './ui-handlers.js';
import { FileManager } from './file-manager.js';
import { SearchHandler } from './search-handler.js';

class GraphVisualizerApp {
    constructor() {
        this.graphData = null;
        this.selectedNodeId = null;
        this.currentHopLevel = 1;
        this.iterationFilter = null;
        this.connectionFilter = null;

        const width = window.innerWidth - 340;
        const height = window.innerHeight;

        this.renderer = new GraphRenderer('graph', width, height);
        this.fileManager = new FileManager();
        this.uiHandlers = null;
        this.searchHandler = null;

        this.setupEventHandlers();
    }

    setupEventHandlers() {
        // 창 크기 변경
        window.addEventListener('resize', () => {
            const newWidth = window.innerWidth - 340;
            const newHeight = window.innerHeight;
            this.renderer.resize(newWidth, newHeight);
        });

        // 배경 클릭
        this.renderer.onBackgroundClick(() => {
            this.renderer.clearAllHighlights();
            this.selectedNodeId = null;
        });

        // Hop 컨트롤
        this.setupHopControls();

        // 전역 함수 등록 (HTML onclick에서 사용)
        window.showFileSelector = () => this.fileManager.showFileSelector();
        window.applyIterationFilter = () => this.applyIterationFilter();
        window.clearIterationFilter = () => this.clearIterationFilter();
        window.applyConnectionFilter = () => this.applyConnectionFilter();
        window.clearConnectionFilter = () => this.clearConnectionFilter();
        window.selectNodeFromSearch = (nodeId) => this.selectNodeFromSearch(nodeId);
    }

    setupHopControls() {
        d3.selectAll('.hop-btn').on('click', (event) => {
            d3.selectAll('.hop-btn').classed('active', false);
            d3.select(event.currentTarget).classed('active', true);
            this.currentHopLevel = parseInt(event.currentTarget.getAttribute('data-hop'));

            if (this.selectedNodeId) {
                this.renderer.highlightNodesMultiHop(this.selectedNodeId, this.currentHopLevel);
            }
        });
    }

    async loadGraph() {
        try {
            this.graphData = await API.getGraphData();

            this.uiHandlers = new UIHandlers(this.graphData);
            this.searchHandler = new SearchHandler(this.graphData);

            this.uiHandlers.displayFileInfo(this.graphData.metadata, this.graphData.topic);

            this.renderer.render(this.graphData, {
                onNodeClick: (event, d) => this.handleNodeClick(event, d),
                onNodeMouseover: (event, d) => this.uiHandlers.handleNodeMouseover(event, d),
                onNodeMouseout: () => this.uiHandlers.handleNodeMouseout()
            });

            this.searchHandler.setup((nodeId) => this.selectNodeFromSearch(nodeId));
            this.uiHandlers.displayStatistics();

        } catch (error) {
            console.error("Error loading graph data:", error);
            this.fileManager.showFileSelector();
        }
    }

    async handleNodeClick(event, d) {
        this.selectedNodeId = d.id;
        this.renderer.highlightNodesMultiHop(d.id, this.currentHopLevel);
        await this.uiHandlers.displayNodeDetails(d.id);
    }

    async selectNodeFromSearch(nodeId) {
        const nodeData = this.graphData.nodes.find(n => n.id === nodeId);
        if (nodeData) {
            this.selectedNodeId = nodeId;
            this.renderer.highlightNodesMultiHop(nodeId, this.currentHopLevel);
            await this.uiHandlers.displayNodeDetails(nodeId);
        }
    }

    applyIterationFilter() {
        const filterValue = parseInt(document.getElementById('iteration-filter').value);
        if (isNaN(filterValue)) return;

        this.iterationFilter = filterValue;
        this.renderer.applyFilters(this.iterationFilter, this.connectionFilter);
    }

    clearIterationFilter() {
        this.iterationFilter = null;
        document.getElementById('iteration-filter').value = '';
        this.renderer.applyFilters(this.iterationFilter, this.connectionFilter);
    }

    applyConnectionFilter() {
        const filterValue = parseInt(document.getElementById('connection-filter').value);
        if (isNaN(filterValue)) return;

        this.connectionFilter = filterValue;
        this.renderer.applyFilters(this.iterationFilter, this.connectionFilter);
    }

    clearConnectionFilter() {
        this.connectionFilter = null;
        document.getElementById('connection-filter').value = '';
        this.renderer.applyFilters(this.iterationFilter, this.connectionFilter);
    }

    async init() {
        try {
            const response = await fetch('/api/graph-data');
            if (response.ok) {
                await this.loadGraph();
            } else {
                this.fileManager.showFileSelector();
            }
        } catch (error) {
            this.fileManager.showFileSelector();
        }

        // 파일 선택 후 그래프 로드
        const originalSelectFile = this.fileManager.selectFile.bind(this.fileManager);
        this.fileManager.selectFile = async (filepath) => {
            const success = await originalSelectFile(filepath);
            if (success) {
                await this.loadGraph();
            }
        };
    }
}

// 앱 초기화
window.addEventListener('DOMContentLoaded', () => {
    const app = new GraphVisualizerApp();
    app.init();
});
