// API 통신 모듈
export const API = {
    async getSavedGraphs() {
        const response = await fetch('/api/saved-graphs');
        return await response.json();
    },

    async loadGraph(filepath) {
        const response = await fetch('/api/load-graph', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ filename: filepath })
        });
        return await response.json();
    },

    async getGraphData() {
        const response = await fetch('/api/graph-data');
        if (!response.ok) {
            throw new Error('No graph loaded');
        }
        return await response.json();
    },

    async getStatistics() {
        const response = await fetch('/api/statistics');
        return await response.json();
    },

    async getNodeDetails(nodeId) {
        const response = await fetch(`/api/node/${nodeId}`);
        return await response.json();
    }
};
