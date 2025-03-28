<script>
    import { uploadFiles } from '$lib/api';
    import FileUpload from '$lib/components/FileUpload.svelte';
    import { goto } from '$app/navigation';
    
    let isUploading = false;
    let uploadResult = null;
    let uploadError = null;
    
    async function handleUpload(event) {
        const { files, fileType } = event.detail;
        isUploading = true;
        uploadResult = null;
        uploadError = null;
        
        try {
            const result = await uploadFiles(files, fileType);
            uploadResult = result;
            
            // Show success for 3 seconds then redirect to chat
            setTimeout(() => {
                goto('/');
            }, 3000);
        } catch (error) {
            console.error('Error uploading files:', error);
            uploadError = error.message || 'An error occurred during upload';
        } finally {
            isUploading = false;
        }
    }
</script>

<svelte:head>
    <title>AI Fitness - Upload Data</title>
</svelte:head>

<div class="upload-page">
    <div class="upload-card">
        <h1>Upload Fitness Data</h1>
        <p class="description">
            Upload your fitness data files to get personalized insights and recommendations.
            We support CSV exports from MyFitnessPal and Garmin Connect.
        </p>
        
        <div class="upload-section">
            <FileUpload on:upload={handleUpload} {isUploading} />
        </div>
        
        {#if uploadResult}
            <div class="alert success">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                    <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
                <div>
                    <h3>Upload Successful!</h3>
                    <p>{uploadResult.message}</p>
                    <p>Redirecting to chat...</p>
                </div>
            </div>
        {/if}
        
        {#if uploadError}
            <div class="alert error">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <div>
                    <h3>Upload Failed</h3>
                    <p>{uploadError}</p>
                </div>
            </div>
        {/if}
        
        <div class="instructions">
            <h2>How to Export Your Data</h2>
            
            <div class="instruction-section">
                <h3>MyFitnessPal</h3>
                <ol>
                    <li>Log in to your MyFitnessPal account on the website</li>
                    <li>Go to "Reports" in the main menu</li>
                    <li>Select the date range you want to export</li>
                    <li>Click on "Export Data" at the bottom of the page</li>
                    <li>Save the CSV files for Nutrition, Exercise, and Measurements</li>
                </ol>
            </div>
            
            <div class="instruction-section">
                <h3>Garmin Connect</h3>
                <ol>
                    <li>Log in to Garmin Connect on the website</li>
                    <li>Click on your profile icon in the top right</li>
                    <li>Select "Settings" then "Account Information"</li>
                    <li>Scroll down to "Data Management" and click "Export Data"</li>
                    <li>Select "Activities" and choose CSV format</li>
                    <li>Click "Export" and save the file</li>
                </ol>
            </div>
        </div>
    </div>
</div>

<style>
    .upload-page {
        display: flex;
        justify-content: center;
        padding: 2rem 0;
    }

    .upload-card {
        background-color: white;
        border-radius: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        padding: 2rem;
        width: 100%;
        max-width: 800px;
    }

    h1 {
        color: #3b82f6;
        margin-top: 0;
        margin-bottom: 1rem;
        text-align: center;
    }

    .description {
        text-align: center;
        color: #6b7280;
        margin-bottom: 2rem;
    }

    .upload-section {
        margin-bottom: 2rem;
    }

    .alert {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
    }

    .success {
        background-color: #ecfdf5;
        color: #065f46;
    }

    .error {
        background-color: #fef2f2;
        color: #b91c1c;
    }

    .alert h3 {
        margin-top: 0;
        margin-bottom: 0.5rem;
    }

    .alert p {
        margin: 0;
    }

    .instructions {
        border-top: 1px solid #e5e7eb;
        padding-top: 2rem;
    }

    .instructions h2 {
        font-size: 1.25rem;
        color: #4b5563;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }

    .instruction-section {
        margin-bottom: 2rem;
    }

    .instruction-section h3 {
        font-size: 1.1rem;
        color: #3b82f6;
        margin-bottom: 1rem;
    }

    ol {
        padding-left: 1.5rem;
        color: #4b5563;
    }

    li {
        margin-bottom: 0.5rem;
    }
</style>
