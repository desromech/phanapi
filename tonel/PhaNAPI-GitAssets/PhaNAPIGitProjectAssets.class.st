"
I am a helper class that is used for locating binary file assets that are versioned along a git project repository.
"
Class {
	#name : #PhaNAPIGitProjectAssets,
	#superclass : #Object,
	#instVars : [
		'session',
		'location'
	],
	#classInstVars : [
		'session',
		'location'
	],
	#category : #'PhaNAPI-GitAssets'
}

{ #category : #hooks }
PhaNAPIGitProjectAssets class >> adjustLocation: repoLocation [
	^ repoLocation
]

{ #category : #hooks }
PhaNAPIGitProjectAssets class >> defaultGithubRepositoryName [
	^ nil
]

{ #category : #hooks }
PhaNAPIGitProjectAssets class >> defaultGithubRepositoryOwners [
	^ #()
]

{ #category : #hooks }
PhaNAPIGitProjectAssets class >> defaultRepositoryBranch [
	^ 'master'
]

{ #category : #private }
PhaNAPIGitProjectAssets class >> findAssets [
	^ PhaNAPIGitProjectAssetsLocator findAssetsForThisSessionSpecifiedIn: self
]

{ #category : #accessing }
PhaNAPIGitProjectAssets class >> location [
	session ~~ Smalltalk session ifTrue: [ 
		location := self findAssets.
		session := Smalltalk session
	].
	^ location
]
