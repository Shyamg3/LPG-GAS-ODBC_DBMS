CREATE SEQUENCE seq_fee_id START WITH 5000 INCREMENT BY 1 NOCACHE NOCYCLE;

CREATE TABLE Student_buffer (
    fee_id NUMBER(5) PRIMARY KEY,
    student_id NUMBER(5) NOT NULL,
    student_name VARCHAR2(50) NOT NULL,
    department VARCHAR2(30) NOT NULL,
    seat_type VARCHAR2(15) CHECK (seat_type IN ('PUDUCHERRY','JOSAA')),
    total_amount NUMBER(8,2) NOT NULL,
    paid_amount NUMBER(8,2) NOT NULL,
    balance_amount NUMBER(8,2) NOT NULL,
    check_id VARCHAR2(10) CHECK (check_id IN ('PAID','PENDING','PARTIAL')),
    due_date DATE NOT NULL,
    payment_date DATE DEFAULT SYSDATE
);

CREATE TABLE Student_main (
    fee_id NUMBER(5) PRIMARY KEY,
    student_id NUMBER(5) NOT NULL,
    student_name VARCHAR2(50) NOT NULL,
    department VARCHAR2(30) NOT NULL,
    seat_type VARCHAR2(15) CHECK (seat_type IN ('PUDUCHERRY','JOSAA')),
    total_amount NUMBER(8,2) NOT NULL,
    paid_amount NUMBER(8,2) NOT NULL,
    balance_amount NUMBER(8,2) NOT NULL,
    check_id VARCHAR2(10) CHECK (check_id IN ('PAID','PENDING','PARTIAL')),
    due_date DATE NOT NULL,
    payment_date DATE DEFAULT SYSDATE
);

select * from student_buffer;
select * from student_main;









