import api from "./api";

export const reportsService = {

    async getExecutiveReport(){

        const { data } = await api.get(
            "/api/v1/reports/executive"
        );

        return data;
    }

}