"
I am an utility that is used to facilitate finding binary assets of GitHub projects that are loaded in Squeak via Metacello baseline scripts.
"
Class {
	#name : #PhaNAPISqueakGitHubProjectAssetsLocator,
	#superclass : #PhaNAPIGitProjectAssetsLocator,
	#category : #'PhaNAPI-Squeak'
}

{ #category : #assets }
PhaNAPISqueakGitHubProjectAssetsLocator >> attemptToFindAssetsForThisSessionSpecifiedIn: assetsSpecClass [
	| githubCacheLocation repoName repoOwners repoBranch |
	githubCacheLocation := FSLocator imageDirectory / 'github-cache'.
	repoName := assetsSpecClass defaultGithubRepositoryName.
	repoName ifNil: [ ^ nil ].

	repoOwners := assetsSpecClass defaultGithubRepositoryOwners.
	repoOwners isEmpty ifTrue: [ ^ nil ].

	repoBranch := assetsSpecClass defaultRepositoryBranch.
	repoBranch ifNil: [ ^ nil ].
	
	repoOwners do: [ :owner |
		| cloneFolderName branchDirectory |
		cloneFolderName := owner , '#' , repoName.
		branchDirectory := githubCacheLocation / cloneFolderName / repoBranch.
		(branchDirectory exists and: [ branchDirectory isDirectory ]) ifTrue: [ 
			branchDirectory children do: [ :eachChild |
				eachChild isDirectory ifTrue: [
					^ assetsSpecClass adjustLocation: eachChild asFileReference
				]
			]
		]
	].

	^ nil
]
