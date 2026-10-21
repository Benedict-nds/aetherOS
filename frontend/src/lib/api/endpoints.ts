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
    reports:{
        lowStock:"/api/reports/low-stock",
        expiry:"/api/reports/expiry",
    },
    dashboard:{
        summary:"/api/dashboard/summary"
    }
}as const
