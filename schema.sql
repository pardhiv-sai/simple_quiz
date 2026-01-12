create extension if not exists "uuid-ossp";

create table if not exists users (
  id uuid default uuid_generate_v4() primary key,
  username text unique not null,
  password text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create table if not exists quizzes (
  id uuid default uuid_generate_v4() primary key,
  title text not null,
  description text,
  duration integer default 600,
  is_visible boolean default true,
  show_score boolean default false,
  allow_reattempts boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create table if not exists questions (
  id uuid default uuid_generate_v4() primary key,
  quiz_id uuid references quizzes(id) on delete cascade not null,
  text text not null,
  image_url text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create table if not exists options (
  id uuid default uuid_generate_v4() primary key,
  question_id uuid references questions(id) on delete cascade not null,
  text text not null,
  is_correct boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now())
);

create table if not exists results (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references users(id) on delete cascade not null,
  quiz_id uuid references quizzes(id) on delete cascade not null,
  score integer not null,
  total_questions integer not null,
  completed_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create table if not exists user_answers (
  id uuid default uuid_generate_v4() primary key,
  result_id uuid references results(id) on delete cascade not null,
  question_id uuid references questions(id) on delete set null,
  selected_option_id uuid references options(id) on delete set null,
  is_correct boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
