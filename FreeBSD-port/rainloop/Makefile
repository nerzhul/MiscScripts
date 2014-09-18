# $FreeBSD$

PORTNAME=	rainloop
PORTVERSION=	1.6.9
CATEGORIES?=	mail www
MASTER_SITES=	SF/${PORTNAME}-webmail/
EXTRACT_SUFX=	.zip

MAINTAINER=	loic.blot@unix-experience.fr
COMMENT=	Modern and interactive webmail

NO_BUILD=	yes
WRKSRC=		${WRKDIR}/${PORTNAME}
DISTNAME=	${PORTNAME}-${PORTVERSION}

WANT_PHP_WEB=   yes
USE_PHP=	curl iconv json xml dom openssl pcre spl
# @TODO: PDO also for different backends

do-install:
	@${MKDIR} -m 0755 ${STAGEDIR}${WWWDIR}
	@cd ${WRKSRC} && ${COPYTREE_SHARE} . ${STAGEDIR}${WWWDIR}

.include <bsd.port.mk>
