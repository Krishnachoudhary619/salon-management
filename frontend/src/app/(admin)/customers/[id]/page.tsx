import { CustomerProfile } from "@/components/customers/customer-profile";

interface CustomerProfilePageProps {
  params: Promise<{ id: string }>;
}

export default async function CustomerProfilePage({ params }: CustomerProfilePageProps) {
  const { id } = await params;
  return <CustomerProfile customerId={id} />;
}
