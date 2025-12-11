export class AppState {
    isAuthenticated = $state(false);
    isLoginModalOpen = $state(false);
    user = $state(null);

    toggleLogin() {
        this.isLoginModalOpen = !this.isLoginModalOpen;
    }

    setAuthenticated(value: boolean) {
        this.isAuthenticated = value;
    }
}

export const appState = new AppState();
