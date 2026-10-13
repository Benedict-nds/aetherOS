export const endpoints = {
    auth:{
        login:"/api/auth/login",
        me:"/api/auth/me",
        logout:"/api/auth/logout",
    },
    medicines:{
        list:"/api/medicines",
        categories:"/api/medicines-categories",
    },
    dashboard:{
        summary:"/api/dashboard/summary"
    }
}as const