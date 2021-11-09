//////////////////////////////////////////////////////////////////////////////
///////////////////// Governor.sol base definitions //////////////////////////
//////////////////////////////////////////////////////////////////////////////
methods {
    proposalSnapshot(uint256) returns uint256 envfree // matches proposalVoteStart
    proposalDeadline(uint256) returns uint256 envfree
    hashProposal(address[],uint256[],bytes[],bytes32) returns uint256 envfree
    isExecuted(uint256) returns bool envfree
    isCanceled(uint256) returns bool envfree
    // initialized(uint256) returns bool envfree

    hasVoted(uint256, address) returns bool

    castVote(uint256, uint8) returns uint256

    // internal functions made public in harness:
    _quorumReached(uint256) returns bool envfree
    _voteSucceeded(uint256) returns bool envfree

    // getter for checking the sums
    counter_vote_power_by_id(uint256) returns uint256 envfree
    ghost_vote_power_by_id(uint256) returns uint256 envfree
    counted_weight(uint256) returns uint256 envfree
}

//////////////////////////////////////////////////////////////////////////////
///////////////////////////////// GHOSTS /////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////

ghost vote_power_ghost() returns uint256;

hook Sstore ghost_vote_power_by_id[KEY uint256 pId] uint256 current_power STORAGE{
    havoc vote_power_ghost assuming vote_power_ghost@new() == vote_power_ghost@old() + current_power;
}


//////////////////////////////////////////////////////////////////////////////
////////////////////////////// INVARIANTS ////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////


/**
 * A proposal cannot end unless it started.
 */
//invariant voteStartBeforeVoteEnd1(uint256 pId) proposalSnapshot(pId) < proposalDeadline(pId)
invariant voteStartBeforeVoteEnd(uint256 pId)
        (proposalSnapshot(pId) > 0 =>  proposalSnapshot(pId) < proposalDeadline(pId))
             && (proposalSnapshot(pId) == 0 => proposalDeadline(pId) == 0)
        /*
        proposalSnapshot(pId) < proposalDeadline(pId) || (proposalSnapshot(pId) == 0 && proposalDeadline(pId) == 0)
        { preserved {
            require initialized(pId) == true;
        }}
        */

/**
 * A proposal cannot be both executed and canceled.
 */
invariant noBothExecutedAndCanceled(uint256 pId) 
        !isExecuted(pId) || !isCanceled(pId)

/**
 * A proposal cannot be neither executed nor canceled before it starts
 */
invariant noExecuteOrCancelBeforeStarting(env e, uint256 pId) 
        e.block.number < proposalSnapshot(pId) 
            => !isExecuted(pId) && !isCanceled(pId)

/**
 * A proposal could be executed only if quorum was reached and vote succeeded
 */
invariant executionOnlyIfQuoromReachedAndVoteSucceeded(uint256 pId) 
        isExecuted(pId) => _quorumReached(pId) && _voteSucceeded(pId)

/*
 * No functions should be allowed to run after a job is deemed as canceled
 */
rule cannotSetIfCanceled(uint256 pId, method f) filtered { f-> !f.isView }{
    require(isCanceled(pId));
    env e; calldataarg args;
    f(e, args);
    assert(isCanceled(pId) => lastReverted == true, "Function did not revert when canceled");
}

/*
 * No functions should be allowed to run after a job is deemed as executed
 */
rule cannotSetIfExecuted(uint256 pId, method f) filtered { f-> !f.isView }{
    require(isExecuted(pId));
    env e; calldataarg args;
    f(e, args);
    assert(isExecuted(pId) => lastReverted == true, "Function did not revert after executed");
}

/*
 * sum of all votes casted is equal to the sum of voting power of those who voted
 */
invariant SumOfVotesCastEqualSumOfPowerOfVoted(uint256 pId)
        counted_weight(pId) == vote_power_ghost()

//////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// RULES ////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////


/**
 * The voting must start not before the proposal’s creation time
 */
rule noStartBeforeCreation(uint256 pId) {
    uint previousStart = proposalSnapshot(pId);
    require previousStart == 0;
    env e;
    calldataarg arg;
    propose(e, arg);

    uint newStart = proposalSnapshot(pId);
    // if created, start is after creation
    assert newStart != 0 => newStart >= e.block.number;
}

/**
 * Check hashProposal hashing is reliable (different inputs lead to different buffers hashed)
 */
 /*
rule checkHashProposal {
    address[] t1;
    address[] t2;
    uint256[] v1;
    uint256[] v2;
    bytes[] c1;
    bytes[] c2;
    bytes32 d1;
    bytes32 d2;

    uint256 h1 = hashProposal(t1,v1,c1,d1);
    uint256 h2 = hashProposal(t2,v2,c2,d2);
    bool equalHashes = h1 == h2;
    assert equalHashes => t1.length == t2.length;
    assert equalHashes => v1.length == v2.length;
    assert equalHashes => c1.length == c2.length;
    assert equalHashes => d1 == d2;
}
*/


/**
 * Once a proposal is created, voteStart and voteEnd are immutable
 */
rule immutableFieldsAfterProposalCreation(uint256 pId, method f) {
    uint _voteStart = proposalSnapshot(pId);
    uint _voteEnd = proposalDeadline(pId);
    require _voteStart > 0; // proposal was created

    env e;
    calldataarg arg;
    f(e, arg);

    uint voteStart_ = proposalSnapshot(pId);
    uint voteEnd_ = proposalDeadline(pId);
    assert _voteStart == voteStart_;
    assert _voteEnd == voteEnd_;
}

/**
* Check if it's possible to vote two time. Relevant to GovernorCountingSimpleHarness.sol contract
*/
rule doubleVoting(uint256 pId, uint8 sup) {
    env e;
    address user = e.msg.sender;

    bool votedCheck = hasVoted(e, pId, user);
    require votedCheck == true;

    castVote@withrevert(e, pId, sup);
    bool reverted = lastReverted;

    assert reverted, "double voting accured";
}

/**
* 
*/
//rule votingSumAndPower(uint256 pId, uint8 sup, method f) {}
