import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// Add a request interceptor
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("token");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Add a response interceptor
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response && error.response.status === 401) {
            // Handle token refresh here
            const refreshToken = localStorage.getItem("refreshToken");
            if (refreshToken) {
                try {
                    const refreshResponse = await axios.post(
                        `${API_URL}/token/refresh/`,
                        {
                            refresh: refreshToken,
                        }
                    );
                    localStorage.setItem("token", refreshResponse.data.access);
                    error.config.headers.Authorization = `Bearer ${refreshResponse.data.access}`;
                    return axios(error.config);
                } catch (err) {
                    localStorage.removeItem("token");
                    localStorage.removeItem("refreshToken");
                    window.location.href = "/login";
                }
            }
        }
        return Promise.reject(error);
    }
);

// Auth services
export const authService = {
    login: async (email, password) => {
        // Use compatibility endpoint which accepts email or username
        const response = await api.post("/token/compat/", {
            email,
            password,
        });
        localStorage.setItem("token", response.data.access);
        localStorage.setItem("refreshToken", response.data.refresh);
        return response.data;
    },

    logout: () => {
        localStorage.removeItem("token");
        localStorage.removeItem("refreshToken");
    },

    register: async (userData) => {
        const response = await api.post("/users/", userData);
        return response.data;
    },

    getCurrentUser: async () => {
        const response = await api.get("/users/users/me/");
        return response.data;
    },

    updateProfile: async (data) => {
        const response = await api.put("/users/update_profile/", data);
        return response.data;
    },
};
