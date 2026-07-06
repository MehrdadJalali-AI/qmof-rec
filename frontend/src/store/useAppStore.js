import { create } from "zustand";

const useAppStore = create((set) => ({
  selectedMaterial: null,

  recommendations: [],

  chatMessages: [],

  loading: false,

  setSelectedMaterial: (material) =>
    set({
      selectedMaterial: material,
    }),

  setRecommendations: (data) =>
    set({
      recommendations: data,
    }),

  addMessage: (message) =>
    set((state) => ({
      chatMessages: [...state.chatMessages, message],
    })),

  setLoading: (value) =>
    set({
      loading: value,
    }),
}));

export default useAppStore;
