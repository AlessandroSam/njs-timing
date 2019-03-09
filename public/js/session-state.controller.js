angular.module('liveTiming').controller('SessionStateController', ['$scope', '$interval', '$http', function($scope, $interval, $http) {
    var PRACTICE = 0;
    var P_STRING = "практика";
    var QUALIFY = 1;
    var Q_STRING = "квалификация";
    var RACE = 2;
    var R_STRING = "гонка";
    var N_STRING = "нет";

    // TODO Обновление данных
    /*
    Возможны варианты:
    1. Обновление по таймингу. Минимум запросов, но проблемы при внезапной смене сессии
    2. Ежесекундное обновление. Куча лишних запросов
    TODO Пересмотреть архитектуру, чтобы общие данные запрашивались в одном месте и могли независимо
    раздаваться всем контроллерам (а не каждый контроллер отдельно просил ту же сессию - session-state и timing,
    а в перспективе и все остальные!)
    */
    $interval(() => {
        $http.get('/session').success(function (sessionData) {
            $scope.timeRemaining = sessionData.timeRemaining;
            $scope.lapsRemaining = sessionData.lapsRemaining;
            
            switch (sessionData.session) {
                case PRACTICE:
                    $scope.session = P_STRING;
                    break;
    
                case QUALIFY:
                $scope.session = Q_STRING;
                    break;
    
                case RACE:
                    $scope.session = R_STRING;
                    $scope.isRace = true;
                    break;
    
                default:
                    $scope.session = N_STRING;
                    return;
            }
    
        }).error(function() {
            $scope.session = "none",
            $scope.timeRemaining = "--:--",
            $scope.lapsRemaining = "--"
        });
    }, 1000);
    
    // TODO сервис для получения данных вместо $http в каждом контроллере (касается и timing)
}]);