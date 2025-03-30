// Update your API endpoint to point to the correct backend URL
const API_BASE_URL = 'http://localhost:8000/api'; // Adjust this to your Python backend URL

export async function queryFitnessData(query, model = "mistralai/Mistral-7B-Instruct-v0.2", includeRecipes = false) {
    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query,
                system_role: "You are a helpful fitness and nutrition assistant.",
                top_k: 7,
                model: model,
                include_recipes: includeRecipes
            }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        return data; // Return the full response object, which may include recipes
    } catch (error) {
        console.error('Error querying fitness data:', error);
        throw error; // Make sure to re-throw the error so it can be caught in the component
    }
}

export async function uploadFiles(files, fileType) {
    try {
        const formData = new FormData();
        
        // Add each file to the form data
        for (const file of files) {
            formData.append('files', file);
        }
        
        // Add the file type
        formData.append('file_type', fileType);
        
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData,
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error uploading files:', error);
        throw error;
    }
}
