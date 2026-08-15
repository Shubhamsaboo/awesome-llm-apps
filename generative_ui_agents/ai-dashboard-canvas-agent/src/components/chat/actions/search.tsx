import { useCopilotAction } from "@copilotkit/react-core";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Check } from "lucide-react";

export const useSearchActions = () => {
  useCopilotAction({
    name: "SearchAgent",
    available: "disabled",
    description: "Search the internet for the query.",
    render: ({ args, status }) => {
      const { request } = args;
      return (
        <Card className="text-sm m-0 rounded-lg p-0 px-1">
          <CardContent className="flex flex-row items-center justify-center p-2">
            {status !== "complete" ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                <div className="truncate">
                  Searching the internet for:{" "}
                  <span className="font-bold">{request}</span>
                </div>
              </>
            ) : (
              <>
                <Check className="h-4 w-4 mr-2 text-accent" />
                <div className="truncate">
                  Searched the internet for:{" "}
                  <span className="font-bold">{request}</span>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      );
    },
  });
};
