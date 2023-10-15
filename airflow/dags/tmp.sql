CREATE TABLE BookingHotel3 (
    Weekday varchar(50),
    Checkin varchar(50),
    Checkout varchar(50),
  	Province varchar(50),
  HotelName varchar(255),
  Location varchar(255),
  RoomType varchar(50),
  Score Float,
  Rating varchar(50),
  Review INT,
  DistanceFromCentre varchar(255),
  Price varchar(50),
  PRIMARY KEY(HotelName,Checkin,Checkout, Location, RoomType, Weekday)
);