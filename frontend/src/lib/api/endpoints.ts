export const endpoints = {
    auth:{
        login:"/api/auth/login",
        me:"/api/auth/me",
        logout:"/api/auth/logout",
    },
    medicines:{
        list:"/api/medicines",
        categories:"/api/medicine-categories",
        batches:(medicineId: number) => `/api/medicines/${medicineId}/batches`,
    },
    sales:{
        create:"/api/sales",
    },
    dashboard:{
        summary:"/api/dashboard/summary"
    }
}as const
