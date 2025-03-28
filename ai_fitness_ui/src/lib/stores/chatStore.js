import { writable } from 'svelte/store';

function createChatStore() {
    const { subscribe, update } = writable({
        messages: [],
        isLoading: false,
        selectedModel: "mistralai/Mistral-7B-Instruct-v0.2"  // Default model
    });

    return {
        subscribe,
        addMessage: (message, isUser = true) => update(state => {
            return {
                ...state,
                messages: [...state.messages, {
                    id: Date.now(),
                    text: message,
                    isUser,
                    timestamp: new Date()
                }]
            };
        }),
        setLoading: (loading) => update(state => {
            return { ...state, isLoading: loading };
        }),
        setModel: (model) => update(state => {
            return { ...state, selectedModel: model };
        }),
        clear: () => update(() => {
            return { 
                messages: [], 
                isLoading: false,
                selectedModel: "mistralai/Mistral-7B-Instruct-v0.2"  // Reset to default model
            };
        })
    };
}

export const chatStore = createChatStore();
