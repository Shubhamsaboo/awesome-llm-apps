import { Heart } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-card mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="border-t border-border pt-8 space-y-4">
          <p className="text-center text-muted-foreground text-sm">
            © 2024 TripCraft AI. All rights reserved.
          </p>
          <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground">
            Made with <Heart className="w-4 h-4 text-red-500 fill-current" /> by{" "}
            <a
              href="https://x.com/mtwn105"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline font-medium"
            >
              Amit Wani
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
