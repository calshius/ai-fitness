<script>
    import { createEventDispatcher } from 'svelte';
    
    export let fileType = 'mfp'; // Default to MyFitnessPal
    export let isUploading = false;
    
    const dispatch = createEventDispatcher();
    let files = [];
    let dragActive = false;
    
    function handleFileChange(e) {
        const fileList = e.target.files;
        if (fileList) {
            files = Array.from(fileList);
        }
    }
    
    function handleDragEnter(e) {
        e.preventDefault();
        e.stopPropagation();
        dragActive = true;
    }
    
    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        dragActive = false;
    }
    
    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        dragActive = false;
        
        if (e.dataTransfer.files) {
            files = Array.from(e.dataTransfer.files);
        }
    }
    
    function handleSubmit() {
        if (files.length > 0 && !isUploading) {
            dispatch('upload', { files, fileType });
        }
    }
    
    function removeFile(index) {
        files = files.filter((_, i) => i !== index);
    }
</script>

<div class="upload-container">
    <div 
        class="dropzone {dragActive ? 'active' : ''}" 
        on:dragenter={handleDragEnter}
        on:dragleave={handleDragLeave}
        on:dragover={handleDragOver}
        on:drop={handleDrop}
    >
        <input 
            type="file" 
            id="file-upload" 
            multiple 
            accept=".csv" 
            on:change={handleFileChange}
            disabled={isUploading}
        />
        <label for="file-upload" class="upload-label">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <span>Drag & drop CSV files or click to browse</span>
        </label>
    </div>
    
    <div class="file-type-selector">
        <label>
            <input type="radio" bind:group={fileType} value="mfp" disabled={isUploading}>
            <span>MyFitnessPal Data</span>
        </label>
        <label>
            <input type="radio" bind:group={fileType} value="garmin" disabled={isUploading}>
            <span>Garmin Data</span>
        </label>
    </div>
    
    {#if files.length > 0}
        <div class="file-list">
            <h3>Selected Files ({files.length})</h3>
            <ul>
                {#each files as file, i}
                    <li>
                        <span class="file-name">{file.name}</span>
                        <button 
                            class="remove-file" 
                            on:click={() => removeFile(i)}
                            disabled={isUploading}
                        >
                            ×
                        </button>
                    </li>
                {/each}
            </ul>
        </div>
    {/if}
    
    <button 
        class="upload-button" 
        on:click={handleSubmit} 
        disabled={files.length === 0 || isUploading}
    >
        {#if isUploading}
            <div class="spinner"></div>
            <span>Uploading...</span>
        {:else}
            <span>Upload Files</span>
        {/if}
    </button>
</div>

<style>
    .upload-container {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        width: 100%;
        max-width: 600px;
        margin: 0 auto;
    }

    .dropzone {
        border: 2px dashed #d1d5db;
        border-radius: 0.5rem;
        padding: 2rem;
        text-align: center;
        transition: all 0.2s;
        background-color: #f9fafb;
    }

    .dropzone.active {
        border-color: #3b82f6;
        background-color: #eff6ff;
    }

    .dropzone input {
        display: none;
    }

    .upload-label {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        cursor: pointer;
        color: #6b7280;
    }

    .upload-label svg {
        color: #3b82f6;
    }

    .file-type-selector {
        display: flex;
        gap: 2rem;
        justify-content: center;
    }

    .file-type-selector label {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
    }

    .file-list {
        background-color: #f9fafb;
        border-radius: 0.5rem;
        padding: 1rem;
    }

    .file-list h3 {
        margin-top: 0;
        margin-bottom: 0.5rem;
        font-size: 1rem;
        color: #374151;
    }

    .file-list ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .file-list li {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid #e5e7eb;
    }

    .file-list li:last-child {
        border-bottom: none;
    }

    .file-name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .remove-file {
        background: none;
        border: none;
        color: #ef4444;
        font-size: 1.25rem;
        cursor: pointer;
        padding: 0 0.5rem;
    }

    .upload-button {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        transition: background-color 0.2s;
    }

    .upload-button:hover:not(:disabled) {
        background-color: #2563eb;
    }

    .upload-button:disabled {
        background-color: #93c5fd;
        cursor: not-allowed;
    }

    .spinner {
        width: 1rem;
        height: 1rem;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: white;
        animation: spin 1s ease-in-out infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }
</style>
