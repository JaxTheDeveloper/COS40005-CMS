import { api } from "./api";

class AuthService {
    async login(email, password) {
        try {
            // Get JWT tokens
            const response = await api.post("/token/", {
                email,
                password,
            });

            // Store tokens
            localStorage.setItem("token", response.data.access);
            localStorage.setItem("refreshToken", response.data.refresh);

            // Get user profile
            const userResponse = await api.get("/users/users/me/");
            localStorage.setItem("user", JSON.stringify(userResponse.data));

            return userResponse.data;
        } catch (error) {
            throw error;
        }
    }

    async logout() {
        localStorage.removeItem("token");
        localStorage.removeItem("refreshToken");
        localStorage.removeItem("user");
    }

    async getCurrentUser() {
        try {
            const token = localStorage.getItem("token");
            if (!token) return null;

            const response = await api.get("/users/users/me/");
            localStorage.setItem("user", JSON.stringify(response.data));
            return response.data;
        } catch (error) {
            localStorage.removeItem("user");
            if (error.response?.status === 401) {
                localStorage.removeItem("token");
                localStorage.removeItem("refreshToken");
                window.location.href = "/login";
            }
            throw error;
        }
    }

    isAuthenticated() {
        return !!localStorage.getItem("token");
    }
}

export const authService = new AuthService();
