// 노드 검색 기능 모듈
export class SearchHandler {
    constructor(graphData) {
        this.graphData = graphData;
        this.searchInput = document.getElementById('node-search-input');
        this.searchResults = document.getElementById('search-results');
    }

    updateGraphData(graphData) {
        this.graphData = graphData;
    }

    setup(onNodeSelect) {
        this.searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            this.searchResults.innerHTML = '';

            if (!query || !this.graphData) {
                return;
            }

            const matches = this.searchNodes(query);

            if (matches.length === 0) {
                this.searchResults.innerHTML = '<div style="padding: 8px; color: #999;">No nodes found</div>';
                return;
            }

            this.displaySearchResults(matches, onNodeSelect);
        });
    }

    searchNodes(query) {
        return this.graphData.nodes.filter(node => {
            if (node.id.toLowerCase().includes(query)) return true;
            if (node.name && node.name.toLowerCase().includes(query)) return true;

            if (node.data) {
                if (node.data.role && node.data.role.toLowerCase().includes(query)) return true;
                if (node.data.content && node.data.content.toLowerCase().includes(query)) return true;
                if (node.data.summary && node.data.summary.toLowerCase().includes(query)) return true;
                if (node.data.context && node.data.context.toLowerCase().includes(query)) return true;
            }

            return false;
        });
    }

    displaySearchResults(matches, onNodeSelect) {
        console.log('Displaying search results:', matches.length);

        matches.slice(0, 10).forEach(node => {
            const resultItem = document.createElement('div');
            resultItem.className = 'search-result-item';
            resultItem.innerHTML = `
                <div class="search-result-id">${node.id}</div>
                <div class="search-result-name">${node.name} (${node.type})</div>
            `;
            resultItem.onclick = () => {
                console.log('Search result clicked:', node.id);
                this.clearSearch();
                onNodeSelect(node.id);
            };
            this.searchResults.appendChild(resultItem);
        });

        if (matches.length > 10) {
            const moreInfo = document.createElement('div');
            moreInfo.style.cssText = 'padding: 8px; color: #666; font-size: 10px;';
            moreInfo.textContent = `...and ${matches.length - 10} more (type more specific query)`;
            this.searchResults.appendChild(moreInfo);
        }
    }

    clearSearch() {
        this.searchInput.value = '';
        this.searchResults.innerHTML = '';
    }
}
