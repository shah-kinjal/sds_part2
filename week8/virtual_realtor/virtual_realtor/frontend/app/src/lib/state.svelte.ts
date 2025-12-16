import { signOut as amplifySignOut } from "aws-amplify/auth";

export class AppState {
    isAuthenticated = $state(false);
    isLoginModalOpen = $state(false);
    user = $state(null);

    toggleLogin() {
        console.log("toggleLogin called. Current:", this.isLoginModalOpen);
        this.isLoginModalOpen = !this.isLoginModalOpen;
        console.log("toggleLogin done. New:", this.isLoginModalOpen);
    }
    
    openLoginModal() {
        console.log("openLoginModal called");
        this.isLoginModalOpen = true;
        console.log("isLoginModalOpen set to:", this.isLoginModalOpen);
    }
    
    closeLoginModal() {
        console.log("closeLoginModal called");
        this.isLoginModalOpen = false;
    }

    setAuthenticated(value: boolean) {
        this.isAuthenticated = value;
    }

    async signOut() {
        console.log("AppState.signOut() called");
        try {
            await amplifySignOut();
            this.isAuthenticated = false;
            this.user = null;
            console.log("✓ Successfully signed out");
        } catch (error) {
            console.error("❌ Error signing out:", error);
        }
    }
}

export const appState = new AppState();
