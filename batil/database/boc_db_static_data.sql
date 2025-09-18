
-- -----------------------------------------------------
-- Initial data insertion (static data)
-- -----------------------------------------------------

/* Reset all rule-related tables */
/* NOTE: Do not run on live db, as this deletes all records from BOC_RULESETS */

DELETE FROM BOC_USER;
DELETE FROM BOC_RULESETS;
DELETE FROM BOC_RULES;
DELETE FROM BOC_RULEGROUPS;

/* Populate RULEGROUPS */

INSERT INTO BOC_RULEGROUPS VALUES( 'deadline'                  , 'Is there a time limit for the players?', 0 );
INSERT INTO BOC_RULEGROUPS VALUES( 'end_without_win'           , 'If the game ends with no players satisfying the primary win condition,', 1 );
INSERT INTO BOC_RULEGROUPS VALUES( 'paradox_action'            , 'Reaching a paradox results in:', 2 );
INSERT INTO BOC_RULEGROUPS VALUES( 'scenario_priority'         , 'When choosing between multiple causally-consistent scenarios:', 3 );
INSERT INTO BOC_RULEGROUPS VALUES( 'viewing_scope'             , 'Are the time-slices after the active one visible?', 4 );
INSERT INTO BOC_RULEGROUPS VALUES( 'unlock_tagscreen_behaviour', 'What is the behaviour of the "lock" and "unlock" tagscreens?', 5 );


/* Populate RULES */

INSERT INTO BOC_RULES VALUES( 'one_day_per_move', 'deadline', 'If there are stones for a player to command and the player does not submit a full set of commands for that turn in under one day, that player loses the game. In case of simultaneous deadline violation, the game ends with no player satisfying the win condition.', 0, '', '', 'One day per move' );
INSERT INTO BOC_RULES VALUES( 'three_days_per_move', 'deadline', 'If there are stones for a player to command and the player does not submit a full set of commands for that turn in under three days, that player loses the game. In case of simultaneous deadline violation, the game ends with no player satisfying the win condition.', 1, '', '', 'Three days per move' );
INSERT INTO BOC_RULES VALUES( 'one_hour_cumulative', 'deadline', 'When opening the game and being prompted for a new turn, a timer starts. Its value is added to a cumulative sum after the full turn is submitted. If this sum exceeds one hour, the player automatically loses the game.', 2, '', '', 'One hour, cumulative' );
INSERT INTO BOC_RULES VALUES( 'one_day_cumulative', 'deadline', 'When opening the game and being prompted for a new turn, a timer starts. Its value is added to a cumulative sum after the full turn is submitted. If this sum exceeds one day, the player automatically loses the game.', 3, '', '', 'One day, cumulative' );
INSERT INTO BOC_RULES VALUES( 'no_deadline', 'deadline', 'There is no deadline. This game cannot end by abandonment.', 4, '', '', 'Open game' );

INSERT INTO BOC_RULES VALUES( 'draw', 'end_without_win', 'The game counts as a draw.', 0, '', '', 'Poiccard''s Gambit' );
INSERT INTO BOC_RULES VALUES( 'win_by_points', 'end_without_win', 'If one player owns the majority of bases in the final timeslice of the last canonised round, that player wins the game.', 1, '', '', 'Fighting in the War Room' );

INSERT INTO BOC_RULES VALUES( 'permanent_removal', 'paradox_action', 'Variations of deactivating stones on setup are tried in a specific order until a causally-consistent scenario is possible. Setup stones deactivated this way stay deactivated for the rest of the game, even if, in future canonizations, their reoccurence would be causally consistent.', 0, 'vol_setup', '', 'Auditors of Reality' );
INSERT INTO BOC_RULES VALUES( 'temporary_removal', 'paradox_action', 'Variations of deactivating stones on setup are tried in a specific order until a causally-consistent scenario is possible.', 1, 'vol_setup', '', 'Hulot''s Holiday' );
INSERT INTO BOC_RULES VALUES( 'game_end', 'paradox_action', 'A paradox immediately ends the game!', 2, 'all_setup', '', 'Know your paradoxes!' );

INSERT INTO BOC_RULES VALUES( 'conserve_setup', 'scenario_priority', '1. Smaller number of setup deactivations is prioritised; 2. Not deactivating setup stones more recently touched by the player is prioritised; 3. Keeping effects added more recently active is prioritised.', 0, '', 'vol_setup', 'Shield and Spear' );
INSERT INTO BOC_RULES VALUES( 'activity_interaction_recency', 'scenario_priority', '1. Not deactivating stones more recently touched by the player is prioritised; 2. Keeping effects added more recently active is prioritised.', 1, '', 'vol_setup', 'Ace Wildcard' );
INSERT INTO BOC_RULES VALUES( 'conserve_effects_stones_hc', 'scenario_priority', '1. Bigger number of active effects is prioritised; 2. Bigger number of stones present on board is prioritised; 3. Keeping more recently added stones is prioritised (where the recency of setup stones is determined in first round by a headcount by each player); 4. Keeping actions added more recently active is prioritised.', 2, '', 'vol_setup', 'Merry Chronos' );
INSERT INTO BOC_RULES VALUES( 'all_setup_activity_recency', 'scenario_priority', 'Keeping effects added more recently active is prioritised.', 0, '', 'all_setup', 'Out with the Old' );
INSERT INTO BOC_RULES VALUES( 'all_setup_conserve_effects', 'scenario_priority', '1. Bigger number of active effects is prioritised; 2. Keeping effects added more recently active is prioritised.', 1, '', 'all_setup', 'Conservative' );

INSERT INTO BOC_RULES VALUES( 'view_entire_board', 'viewing_scope', 'Yes, the players can view the entire board', 0, '', '', 'Omniscience' );
INSERT INTO BOC_RULES VALUES( 'hide_future', 'viewing_scope', 'The players can only view time-slices up to and including the active one. This means they cannot see the ante-effects placed by the opponent in the previous round.', 1, '', '', 'Fog of War' );

INSERT INTO BOC_RULES VALUES( 'presence', 'unlock_tagscreen_behaviour', 'If both "unlock" and "lock" are present, they cancel each other out, regardless of the number of tagscreens of each type.', 0, '', '', 'Antidote' );
INSERT INTO BOC_RULES VALUES( 'saturation', 'unlock_tagscreen_behaviour', 'The difference between the number of "unlock" and "lock" tagscreens for each stone is calculated in each time-slice. If negative, lock state is forced. If zero, nothing happens. If positive, stones in lock state become unlocked and unlocked states are interfered with.', 1, '', '', 'Tug-o-war' );

/* Initialise home.index tutorial */

INSERT INTO BOC_TREE_DOCUMENTS (LABEL, CONTENT, VIEWER, PARENT_CHAPTER) VALUES ('Welcome', '<p>Welcome to Batil (BAttle in TIme Loops)!</p><p>This guide is divided into two parts. The first will teach you how to navigate the Batil website and how to start playing the game right away. The second is a complete rulebook for Batil, including example scenarios which you can explore in-game by clicking on the interactive links inside the tutorial text.</p><p>If you''re reading this, the first ''beta'' version of the game has been deployed to a live server. Please keep track of any issues, wanted features, unwanted bugs, unclear explanations, or comments regarding the rules of the game that you might have and send them to me either via this (TODO LINK) feedback submission form (/TODO) or via my e-mail address michael.horansky@gmail.com. If you won''t, I will send you unsolicited emails on the address you provided during registration, where I will spam you with tedious multi-page feedback forms. Thank you for being a cooperating test subject.</p><p>Enjoy the game!</p>', 'tutorial_guide', NULL);

/* Initialise rating model */

INSERT INTO BOC_RATING_PARAMETERS (PARAMETER_NAME, PARAMETER_VALUE) VALUES ('INITIAL_RATING', 1000.0);
INSERT INTO BOC_RATING_PARAMETERS (PARAMETER_NAME, PARAMETER_VALUE) VALUES ('RATING_DIFFERENCE_SCALE', 400.0);
INSERT INTO BOC_RATING_PARAMETERS (PARAMETER_NAME, PARAMETER_VALUE) VALUES ('INITIAL_ESTIMATE_DRAW_PROBABILITY', 0.1);
INSERT INTO BOC_RATING_PARAMETERS (PARAMETER_NAME, PARAMETER_VALUE) VALUES ('INITIAL_ESTIMATE_HANDICAP_STD', 120.0);
INSERT INTO BOC_RATING_PARAMETERS (PARAMETER_NAME, PARAMETER_VALUE) VALUES ('RATING_ADJUSTMENT_STEP_SCALE', 32.0);
INSERT INTO BOC_RATING_PARAMETERS (PARAMETER_NAME, PARAMETER_VALUE) VALUES ('RIGIDITY', 10.0);
INSERT INTO BOC_RATING_PARAMETERS (PARAMETER_NAME, PARAMETER_VALUE) VALUES ('FREEZING_CONDITION', NULL);

INSERT INTO BOC_HOUSEKEEPING_LOGS (D_PERFORMED) VALUES ('SCHEDULED');



