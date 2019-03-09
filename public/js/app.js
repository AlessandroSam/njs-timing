var liveTiming = angular.module("liveTiming", ['ui.router']);

liveTiming.config(['$stateProvider', function($stateProvider) {
    var states = [
        {
            name: 'dashboard',
            url: '/dashboard',
            template: `<div>Dashboard goes here</div>`
        },
        { 
            name: 'timing', 
            url: '/timing', 
            // Using component: instead of template:
            component: 'timing'
        },
        {
            name: 'analysis',
            url: '/analysis',
            template: `<div>Analysis goes here</div>`
        },
        {
            name: 'settings',
            url: '/settings',
            template: `<div>Settings goes here</div>`
        }
    ];
      
    // Loop over the state definitions and register them
    states.forEach(function(state) {
        $stateProvider.state(state);
    });
}]);