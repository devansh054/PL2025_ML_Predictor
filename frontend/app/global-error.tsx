'use client';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <div className="min-h-screen bg-black text-white flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-3xl font-bold mb-4">Something went wrong!</h2>
            <p className="text-gray-400 mb-6">A global error occurred.</p>
            <button
              onClick={() => reset()}
              className="bg-[#37003c] hover:bg-[#37003c]/80 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
