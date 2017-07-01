var express = require('express');
var bodyParser = require('body-parser');

var app = express();app.use(bodyParser.json());

const FALLBACK_STR = "{\"session\": -1}";
var currentJson = FALLBACK_STR;

var fastestLap = {
  driverName: "",
  bestLap: -1,
  carName: "",
  lapNumber: -1
};
var flReset = {
  driverName: "",
  bestLap: -1,
  carName: "",
  lapNumber: -1
}

var jsonLogCount = 0;
const jsonLogMax = 5;

app.listen(8080, function () {
  console.log('App is listening on port 8080');
})

app.use(express.static('public'));

app.post('/ACTiming2/live', function(req, res, next) {
  if (req.body.session == 2) { // RACE
    if (req.body.cars[0].lapsCompleted > 0) {
      if (fastestLap.bestLap == -1) {
        fastestLap.bestLap = req.body.cars[0].bestLap;
        fastestLap.driverName = req.body.cars[0].driverName;
        fastestLap.carName = req.body.cars[0].carName;
        fastestLap.lapNumber = req.body.cars[0].lapsCompleted;
      }
      req.body.cars.forEach(car => {
        if (car.bestLap < fastestLap.bestLap && car.bestLap > 0) {
          fastestLap.bestLap = car.bestLap;
          fastestLap.driverName = car.driverName;
          fastestLap.carName = car.carName;
          fastestLap.lapNumber = car.lapsCompleted;
        }
      });
    } else {
      fastestLap = flReset;
    }

  }
  req.body.fastestLap = fastestLap;
  if (jsonLogCount < jsonLogMax) {
    console.log(req.body);
    jsonLogCount++;
  }
  currentJson = req.body;
})

app.get('/', function(req, res, next) {
  res.sendFile(__dirname + '/public/livetiming.html');
});

app.get('/ACTiming2/live', function(req, res, next) {
  res.send(currentJson);
})
