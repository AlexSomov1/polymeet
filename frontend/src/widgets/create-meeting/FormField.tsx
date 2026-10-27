import { cn } from "@/lib/utils";

interface FormFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function FormField({ label, error, className, ...props }: FormFieldProps) {
  return (
    <div className="space-y-2">
      <label className="text-xs font-medium text-slate-400">
        {label}
        {props.required && <span className="ml-0.5 text-red-400">*</span>}
      </label>
      <input
        className={cn(
          "w-full rounded-lg border bg-white/5 px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none",
          error ? "border-red-500" : "border-white/10 focus:border-blue-500",
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}