-- 1) create sequence for Booking_ID
CREATE SEQUENCE seq_booking_id START WITH 1000 INCREMENT BY 1 NOCACHE NOCYCLE;

-- 2) master table CONS_DET
CREATE TABLE CONS_DET (
    Customer_ID        NUMBER PRIMARY KEY,
    Name               VARCHAR2(50) NOT NULL,
    Address            VARCHAR2(100),
    Mobile_Number      VARCHAR2(10) UNIQUE NOT NULL,
    Email              VARCHAR2(50) UNIQUE,
    Aadhaar_Number     VARCHAR2(12) UNIQUE NOT NULL,
    Connection_Type    VARCHAR2(20),
    Created_Date       DATE DEFAULT SYSDATE,
    State              VARCHAR2(30),
    Pincode            VARCHAR2(6),
    Connection_Number  NUMBER
);

-- 3) bookings table
CREATE TABLE BOOKINGS (
    Booking_ID         NUMBER PRIMARY KEY,
    Customer_ID        NUMBER,
    Booking_Date       DATE DEFAULT SYSDATE,
    Delivery_Date      DATE,
    Quantity           NUMBER CHECK (Quantity > 0),
    Price_Per_Cylinder NUMBER CHECK (Price_Per_Cylinder > 0),
    Total_Amount       NUMBER,
    Delivery_Status    VARCHAR2(20),
    Days_To_Deliver    NUMBER,
    Payment_Mode       VARCHAR2(20),
    Remaining_Amount   NUMBER
);

-- 4) foreign key from bookings -> cons_det
ALTER TABLE BOOKINGS
ADD CONSTRAINT fk_bookings_cons
FOREIGN KEY (Customer_ID)
REFERENCES CONS_DET(Customer_ID);
