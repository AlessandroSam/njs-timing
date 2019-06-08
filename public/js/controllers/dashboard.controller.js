(function() {
    angular.module('liveTiming').controller('DashboardController', ['$scope', '$interval', '$http', function($scope, $interval, $http) {
        var interval = 5000;
        $scope.gaps = [];
        $scope.lapData = [];
        $interval(function () {
            var PRACTICE = 0;
            var QUALIFY = 1;
            var RACE = 2;

            $http.get('/ACTiming2/live?brief=0').success(function (data) {
                // TODO Прототип. Будет переписано на WS и обработка уйдёт на бэкенд
                $scope.timingData = data;
                $scope.timeLeftView = ($scope.timingData.timeLeft < 0) ? 0 : $scope.timingData.timeLeft;
                if (data.session < 0) {
                    interval = 10000;
                    return;
                } else {
                    interval = 5000;
                }
                let playerPos = 0;
                let playerCar = null;
                $scope.timingData.cars.forEach((car, i) => {
                    if (car.carId == 0) {
                        playerPos = i;
                        playerCar = car;
                    } 
                });
                let minPos = (playerPos - 1) >= 0 ? playerPos - 1: 0;
                let maxPos = (playerPos + 2) <= $scope.timingData.cars.length ? playerPos + 2 : $scope.timingData.cars.length;
                let nearbyCars = $scope.timingData.cars.slice(minPos, maxPos);
                $scope.gaps = nearbyCars.map(car => {
                    // На данном этапе подразумеваем, что машины отсортированы по позициям
                    let gap = car.totalTime - playerCar.totalTime;
                    return {
                        driverName: car.driverName,
                        gap: gap
                    };
                });
                console.log('playerCar: ' + JSON.stringify(playerCar));
                console.log('gap car count: '+ $scope.gaps.length);
            });
        }, interval);
    }]);
})();
