import { writable } from 'svelte/store';

function createChatStore() {
    const { subscribe, update } = writable({
        messages: [],
        isLoading: false
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
        clear: () => update(() => {
            return { messages: [], isLoading: false };
        })
    };
}

export const chatStore = createChatStore();
