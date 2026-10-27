import { cn } from "@/lib/utils";

interface FormTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
}

export function FormTextarea({ label, className, ...props }: FormTextareaProps) {
  return (
    <div className="space-y-2">
      <label className="text-xs font-medium text-slate-400">{label}</label>
      <textarea
        className={cn(
          "w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:border-blue-500 focus:outline-none",
          className
        )}
        {...props}
      />
    </div>
  );
}