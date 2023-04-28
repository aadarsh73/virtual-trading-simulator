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
    stock_name varchar(20) not null,
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
    client_id varchar(20) primary key not null,
    stock_id varchar(20) not null,
    quantity int,
    stock_value int,
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

EXEC update_transaction('123456', 'Withdrawal', 500);