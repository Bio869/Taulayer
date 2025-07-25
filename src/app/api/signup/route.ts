// In src/app/api/signup/route.ts
import { Resend } from 'resend';
import { NextResponse } from 'next/server';

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { fullName, email, companyName, role, useCase } = body;

    const { data, error } = await resend.emails.send({
      from: 'OptimizeAI Signup <info@taulayer.com>', // Use an address from your verified domain
      to: ['pinipur@gmail.com'], // The email address you want to receive submissions
      subject: 'New Signup for OptimizeAI!',
      html: `
        <h1>New Signup Submission</h1>
        <p><strong>Full Name:</strong> ${fullName}</p>
        <p><strong>Email:</strong> ${email}</p>
        <p><strong>Company:</strong> ${companyName || 'N/A'}</p>
        <p><strong>Role:</strong> ${role || 'N/A'}</p>
        <p><strong>Use Case:</strong> ${useCase || 'N/A'}</p>
      `,
    });

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ message: "Email sent successfully!" });

  } catch (error) {
    return NextResponse.json({ error: 'Something went wrong.' }, { status: 500 });
  }
}