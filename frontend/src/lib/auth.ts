// Client-side auth utilities
// Tokens stored in localStorage — simple for now, upgrade to httpOnly cookies post-launch

export const getToken = (): string | null => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("arcanum_token");
};

export const setToken = (token: string): void => {
  localStorage.setItem("arcanum_token", token);
};

export const removeToken = (): void => {
  localStorage.removeItem("arcanum_token");
};

export const getUsername = (): string | null => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("arcanum_username");
};

export const setUsername = (username: string): void => {
  localStorage.setItem("arcanum_username", username);
};

export const removeUsername = (): void => {
  localStorage.removeItem("arcanum_username");
};