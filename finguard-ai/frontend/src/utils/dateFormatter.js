export const IST_OPTIONS = {
  timeZone: "Asia/Kolkata",
};

export const formatDateTime = (date) => {
  if (!date) return "N/A";

  return new Date(date).toLocaleString("en-IN", {
    ...IST_OPTIONS,
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });
};

export const formatDate = (date) => {
  if (!date) return "N/A";

  return new Date(date).toLocaleDateString("en-IN", {
    ...IST_OPTIONS,
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
};