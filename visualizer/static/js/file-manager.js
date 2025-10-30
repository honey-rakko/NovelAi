// 파일 선택 및 관리 모듈
import { API } from './api.js';

export class FileManager {
    constructor() {
        this.currentFile = null;
    }

    showFileSelector() {
        this.loadSavedGraphs();
        document.getElementById('file-selector-modal').classList.remove('hidden');
    }

    hideFileSelector() {
        document.getElementById('file-selector-modal').classList.add('hidden');
    }

    async loadSavedGraphs() {
        try {
            const files = await API.getSavedGraphs();
            const fileList = document.getElementById('file-list');
            fileList.innerHTML = '';

            if (files.length === 0) {
                fileList.innerHTML = '<p style="color: #999;">No saved graph files found in saved_graphs/ directory</p>';
                return;
            }

            files.forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.onclick = () => this.selectFile(file.path);

                const nodeStats = file.node_counter || {};

                fileItem.innerHTML = `
                    <div class="file-item-title">${file.topic}</div>
                    <div class="file-item-details">
                        <div>${file.filename}</div>
                        <div class="file-stats">
                            <span class="stat-badge">Total: ${file.node_count} nodes</span>
                            ${nodeStats.character ? `<span class="stat-badge">Characters: ${nodeStats.character}</span>` : ''}
                            ${nodeStats.event ? `<span class="stat-badge">Events: ${nodeStats.event}</span>` : ''}
                            ${nodeStats.info ? `<span class="stat-badge">Info: ${nodeStats.info}</span>` : ''}
                            ${nodeStats.placeholder ? `<span class="stat-badge">Placeholders: ${nodeStats.placeholder}</span>` : ''}
                        </div>
                    </div>
                `;

                fileList.appendChild(fileItem);
            });
        } catch (error) {
            console.error("Error loading saved graphs:", error);
            document.getElementById('file-list').innerHTML = '<p style="color: red;">Error loading files</p>';
        }
    }

    async selectFile(filepath) {
        try {
            const result = await API.loadGraph(filepath);

            if (result.success) {
                this.currentFile = filepath;
                this.hideFileSelector();
                return true;
            } else {
                alert('Error loading file: ' + result.error);
                return false;
            }
        } catch (error) {
            console.error("Error selecting file:", error);
            alert('Error loading file');
            return false;
        }
    }
}
