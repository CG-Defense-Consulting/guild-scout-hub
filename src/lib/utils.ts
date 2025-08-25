import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Determines the color variant for a closed contract based on its stage
 * @param isClosed - Whether the contract is closed
 * @param currentStage - The current stage of the contract
 * @returns Object with variant and custom classes for styling
 */
export function getClosedStatusStyle(isClosed: boolean | null, currentStage?: string) {
  if (!isClosed) {
    return {
      variant: "secondary" as const,
      customClasses: ""
    };
  }

  // Check if contract is at or past "Awarded" stage
  const isPastAwarded = ['Awarded', 'Production', 'Delivered', 'Paid'].includes(currentStage || '');
  
  if (isPastAwarded) {
    return {
      variant: "default" as const,
      customClasses: "bg-green-100 text-green-800 border-green-200"
    };
  } else {
    return {
      variant: "destructive" as const,
      customClasses: ""
    };
  }
}

/**
 * Gets the appropriate dot color for closed status indicators
 * @param isClosed - Whether the contract is closed
 * @param currentStage - The current stage of the contract
 * @returns Tailwind CSS class for the dot color
 */
export function getClosedStatusDotColor(isClosed: boolean | null, currentStage?: string) {
  if (!isClosed) return "bg-gray-400";
  
  // Check if contract is at or past "Awarded" stage
  const isPastAwarded = ['Awarded', 'Production', 'Delivered', 'Paid'].includes(currentStage || '');
  
  return isPastAwarded ? "bg-green-500" : "bg-red-500";
}
