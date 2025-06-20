import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET() {
  try {
    const tripPlans = await prisma.tripPlan.findMany({
      orderBy: {
        createdAt: 'desc'
      }
    });

    return NextResponse.json(
      {
        success: true,
        tripPlans
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Error fetching trip plans:', error);
    return NextResponse.json(
      {
        success: false,
        message: 'Failed to fetch trip plans'
      },
      { status: 500 }
    );
  }
}