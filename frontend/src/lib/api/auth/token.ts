/* 
REMEMEBER LATER TO CHANGE COMPLETE IMPLEMENTATION TO USE 
COOKIES AS LOCAL AND SESSION STORAGE ARE TO IDEAL SECURITY WAYS 
*/

const TOKEN_KEY = 'aetherqore_token'

export function getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY) ?? sessionStorage.getItem(TOKEN_KEY)
}


export function setToken(token: string, keepSignedIn: boolean): void {
    clearToken()
    const store = keepSignedIn ? localStorage : sessionStorage 
    store.setItem(TOKEN_KEY, token)
}


export function clearToken(): void {
    localStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(TOKEN_KEY)
}