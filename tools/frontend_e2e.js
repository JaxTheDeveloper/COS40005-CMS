const axios = require("axios");
(async () => {
    try {
        const loginResp = await axios.post(
            "http://localhost:8000/api/token/",
            {
                email: "student_all@example.com",
                password: "password123",
            },
            { headers: { "Content-Type": "application/json" } }
        );

        console.log("Got tokens");
        const access = loginResp.data.access;
        console.log("ACCESS:", access);

        const ticketResp = await axios.post(
            "http://localhost:8000/api/core/tickets/",
            {
                title: "FE E2E Ticket (node)",
                description: "Created by headless frontend e2e script",
            },
            { headers: { Authorization: `Bearer ${access}` } }
        );

        console.log("Ticket created:", ticketResp.data);
    } catch (err) {
        if (err.response) {
            console.error("Error status:", err.response.status);
            console.error("Error data:", err.response.data);
        } else {
            console.error(err);
        }
        process.exit(1);
    }
})();
