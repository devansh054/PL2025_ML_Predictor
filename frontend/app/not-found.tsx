import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-6xl font-bold mb-4">404</h2>
        <h3 className="text-2xl font-bold mb-4">Page Not Found</h3>
        <p className="text-gray-400 mb-6">Could not find the requested resource.</p>
        <Link
          href="/"
          className="bg-[#37003c] hover:bg-[#37003c]/80 text-white px-6 py-3 rounded-lg font-medium transition-colors inline-block"
        >
          Return Home
        </Link>
      </div>
    </div>
  );
}
