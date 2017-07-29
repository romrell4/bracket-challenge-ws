CREATE TABLE users (
  user_id  INT AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  name     VARCHAR(30) NOT NULL,

  PRIMARY KEY (user_id),

  UNIQUE (username)
);

CREATE TABLE tournaments (
  tournament_id     INT AUTO_INCREMENT,
  name              VARCHAR(30) NOT NULL,
  master_bracket_id INT,

  PRIMARY KEY (tournament_id)
);

CREATE TABLE players (
  player_id INT AUTO_INCREMENT,
  name      VARCHAR(50) NOT NULL,

  PRIMARY KEY (player_id)
);

CREATE TABLE brackets (
  bracket_id    INT AUTO_INCREMENT,
  user_id       INT,
  tournament_id INT         NOT NULL,
  name          VARCHAR(30) NOT NULL,

  PRIMARY KEY (bracket_id),

  INDEX user_id_index (user_id),
  FOREIGN KEY (user_id)
  REFERENCES users (user_id)
    ON DELETE RESTRICT,

  INDEX tournament_id_index (tournament_id),
  FOREIGN KEY (tournament_id)
  REFERENCES tournaments (tournament_id)
    ON DELETE RESTRICT
);

CREATE TABLE matches (
  match_id   INT AUTO_INCREMENT,
  bracket_id INT NOT NULL,
  round      INT NOT NULL,
  position   INT NOT NULL,
  player1_id INT,
  player2_id INT,
  seed1      INT,
  seed2      INT,
  winner_id  INT,

  PRIMARY KEY (match_id),

  INDEX bracket_id_index (bracket_id),
  FOREIGN KEY (bracket_id)
  REFERENCES brackets (bracket_id)
    ON DELETE RESTRICT,

  INDEX player1_id_index (player1_id),
  FOREIGN KEY (player1_id)
  REFERENCES players (player_id)
    ON DELETE RESTRICT,

  INDEX player2_id_index (player2_id),
  FOREIGN KEY (player2_id)
  REFERENCES players (player_id)
    ON DELETE RESTRICT,

  INDEX winner_id_index (winner_id),
  FOREIGN KEY (winner_id)
  REFERENCES players (player_id)
    ON DELETE RESTRICT
);

