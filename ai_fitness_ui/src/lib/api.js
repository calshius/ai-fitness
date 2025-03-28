const API_URL = 'http://localhost:8000/api';

export async function queryFitnessData(query, systemRole = "You are a helpful fitness and nutrition assistant.", topK = 5) {
    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query,
                system_role: systemRole,
                top_k: topK
            }),
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        return data.response;
    } catch (error) {
        console.error('Error querying fitness data:', error);
        throw error;
    }
}

export async function uploadFiles(files, fileType) {
    try {
        const formData = new FormData();
        
        files.forEach(file => {
            formData.append('files', file);
        });
        
        formData.append('file_type', fileType);

        const response = await fetch(`${API_URL}/upload`, {
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
