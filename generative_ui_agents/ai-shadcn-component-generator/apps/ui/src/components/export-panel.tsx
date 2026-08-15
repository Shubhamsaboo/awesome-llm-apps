import { useState } from "react";
import { CodeBlock } from "./ui/code-block";
import { treeToJsx } from "@/lib/tree-to-jsx";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "./ui/sheet";
import { Button } from "./ui/button";
import { CheckIcon, CopyIcon } from "lucide-react";

export function ExportPanel({
  open,
  onOpenChange,
  tree,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tree: unknown[];
}) {
  const [copied, setCopied] = useState(false);
  const { code } = treeToJsx(tree);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="sm:max-w-lg w-full">
        <SheetHeader>
          <div className="flex items-center justify-between pr-8">
            <div>
              <SheetTitle>Export Component</SheetTitle>
              <SheetDescription>Copy-paste ready React code</SheetDescription>
            </div>
            <Button variant="outline" size="sm" onClick={handleCopy} className="gap-1.5">
              {copied ? (
                <>
                  <CheckIcon className="size-3.5" />
                  Copied
                </>
              ) : (
                <>
                  <CopyIcon className="size-3.5" />
                  Copy
                </>
              )}
            </Button>
          </div>
        </SheetHeader>
        <div className="flex-1 overflow-auto px-4 pb-4">
          <CodeBlock code={code} language="tsx" />
        </div>
      </SheetContent>
    </Sheet>
  );
}
