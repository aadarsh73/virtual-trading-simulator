create table client(
    client_id varchar(20) primary key,
    client_name varchar(20) not null,
    balance int,
    pass varchar(20),
    email varchar(20),
    isadmin int,
    active int
);

create table stock(
    stock_id varchar(20) primary key,
    stock_name varchar(30) not null,
    symbl varchar(10) not null
);

create table tax(
    order_limit int primary key not null,
    charges int not null
);

create table orders(
    order_id varchar(20) primary key,
    client_id varchar(20) not null,
    stock_id varchar(20) not null,
    price int not null,
    quantity int,
    order_type varchar(10),
    date_time timestamp,
    charges int,
    total int,
    foreign key (client_id) references client(client_id),
    foreign key (stock_id) references stock(stock_id)
);

create table watchlist(
    client_id varchar(20) not null,
    stock_id varchar(20) not null,
    foreign key (client_id) references client(client_id),
    foreign key (stock_id) references stock(stock_id),
    primary key (client_id,stock_id)
);

create table portfolio(
    client_id varchar(20) not null,
    stock_id varchar(20) not null,
    quantity int,
    stock_value int,
    primary key (client_id,stock_id),
    foreign key (client_id) references client(client_id),
    foreign key (stock_id) references stock(stock_id)
);

create table transaction(
    client_id varchar(20) not null,
    tid varchar(20) primary key not null,
    transaction_type varchar(10),
    transaction_date timestamp,
    amount int,
    foreign key (client_id) references client(client_id)
);

ALTER TABLE transaction ADD final_balance INT;


create table price_history(
    stock_id varchar(20) not null,
    price int,
    date_time timestamp,
    foreign key (stock_id) references stock(stock_id),
    primary key (stock_id,date_time)
);

CREATE OR REPLACE TRIGGER check_balance_trigger
BEFORE UPDATE ON client
FOR EACH ROW
BEGIN
  IF (:NEW.balance<0) THEN
    RAISE_APPLICATION_ERROR(-20001, 'Insufficient balance');
  END IF;
END;
/

CREATE OR REPLACE PROCEDURE update_transaction(client_id_in IN VARCHAR2, transaction_type_in IN VARCHAR2, amount_in IN NUMBER) AS
  l_tid VARCHAR2(20);
  bal int;
BEGIN
  SELECT MAX(TO_NUMBER(tid)) + 1 INTO l_tid FROM transaction;
  select balance into bal from client where client_id=client_id_in;
  IF l_tid IS NULL THEN
    l_tid := '1';
  END IF;
  INSERT INTO transaction VALUES (client_id_in, l_tid, transaction_type_in, SYSDATE, amount_in, bal);
END;
/

CREATE OR REPLACE PROCEDURE buy_stock(
    p_client_id IN VARCHAR2,
    p_stock_id IN VARCHAR2,
    p_quantity IN NUMBER,
    p_price IN NUMBER
)
IS
    v_order_id VARCHAR2(20);
    v_stock_id int;
    temp_stock varchar2(50);
    v_charges decimal(10,2);
    l_tid NUMBER;
    total decimal(10,2);
    temp1 varchar2(50);
BEGIN


    SELECT MAX(TO_NUMBER(order_id)) + 1 INTO l_tid FROM orders;
    IF l_tid IS NULL THEN
        l_tid := '1';
    END IF;
    v_charges:=0.001*p_price*p_quantity;
    v_order_id := TO_CHAR(l_tid);
    select stock_id into temp_stock from stock where symbl=p_stock_id;
    total := p_price*p_quantity + v_charges;
    update client set balance=balance-total where client_id=p_client_id;
    temp1:= 'Bought ' || p_stock_id || ' Qty. ' || p_quantity;
    insert into orders values (v_order_id, p_client_id, temp_stock, p_price, p_quantity, 'SELL', SYSDATE, v_charges, total);
    update_transaction(p_client_id, temp1, total);
END;
/


CREATE OR REPLACE PROCEDURE sell_stock(
    p_client_id IN VARCHAR2,
    p_stock_id IN VARCHAR2,
    p_quantity IN NUMBER,
    p_price IN NUMBER
)
IS
    v_order_id VARCHAR2(20);
    v_stock_id int;
    temp_stock varchar2(50);
    v_charges decimal(10,2);
    l_tid NUMBER;
    total decimal(10,2);
    temp1 varchar2(50);
    check_quantity int;
BEGIN


    SELECT MAX(TO_NUMBER(order_id)) + 1 INTO l_tid FROM orders;
    IF l_tid IS NULL THEN
        l_tid := '1';
    END IF;
    v_charges:=0.001*p_price*p_quantity;
    v_order_id := TO_CHAR(l_tid);
    select stock_id into temp_stock from stock where symbl=p_stock_id;
    update portfolio set quantity=quantity-p_quantity where client_id=p_client_id and stock_id=temp_stock;
    select quantity into check_quantity from portfolio where client_id=p_client_id and stock_id=temp_stock;
    if check_quantity=0 then
        delete from portfolio where client_id=p_client_id and stock_id=temp_stock;
    end if;
    total := p_price*p_quantity - v_charges;
    update client set balance=balance+total where client_id=p_client_id;
    temp1:= 'Sold ' || p_stock_id || ' Qty. ' || p_quantity;
    insert into orders values (v_order_id, p_client_id, temp_stock, p_price, p_quantity, 'BUY', SYSDATE, v_charges, total);
    update_transaction(p_client_id, temp1, total);
END;
/



EXEC update_transaction('123456', 'Withdrawal', 500);


alter table orders modify price decimal(10,2) not null;
alter table orders modify charges decimal(10,2) not null;
alter table orders add total decimal(10,2) not null;
alter table client modify balance decimal(10,2) not null;
alter table transaction modify amount decimal(10,2) not null;