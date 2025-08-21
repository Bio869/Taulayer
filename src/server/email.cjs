require("dotenv").config();
const express = require("express");
const cors = require("cors");
const { Resend } = require("resend");

const app = express();

app.use(cors());
app.use(express.json());

// pick up key from Render env OR local .env
const resend = new Resend(process.env.RESEND_API_KEY);

// health check (optional, but useful for Render pings)
app.get("/", (req, res) => {
  res.send("✅ Backend is running!");
});

app.post("/send", async (req, res) => {
  const { fullName, email, companyName, role, useCase } = req.body;

  try {
    const { error } = await resend.emails.send({
      from: "OptimizeAI <onboarding@resend.dev>",
      to: ["pinipur@gmail.com"], // 👈 change to your real email later
      subject: "New Signup for τLayer!",
      html: `
        <h2>🚀 New Signup Received</h2>
        <p><strong>Full Name:</strong> ${fullName}</p>
        <p><strong>Email:</strong> ${email}</p>
        <p><strong>Company:</strong> ${companyName || "N/A"}</p>
        <p><strong>Role:</strong> ${role || "N/A"}</p>
        <p><strong>Use Case:</strong> ${useCase || "N/A"}</p>
        <hr />
        <p>Sent automatically via Resend API from the τLayer site.</p>
      `,
    });

    if (error) {
      console.error("❌ Resend error:", error);
      return res.status(500).json({ error: error.message });
    }

    return res.status(200).json({ message: "✅ Email sent!" });
  } catch (err) {
    console.error("❌ Unhandled error:", err);
    return res.status(500).json({ error: "Failed to send email." });
  }
});

// use Render’s PORT env variable, fallback to 3001 for local dev
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`✅ Server running on port ${PORT}`));
