/*************************************************************************

 hypervolume computation

 ---------------------------------------------------------------------

                       Copyright (c) 2010
                  Carlos M. Fonseca <cmfonsec@dei.uc.pt>
             Manuel Lopez-Ibanez <manuel.lopez-ibanez@ulb.ac.be>
                    Luis Paquete <paquete@dei.uc.pt>
      Andreia P. Guerreiro <andreia.guerreiro@ist.utl.pt>

 This program is free software (software libre); you can redistribute
 it and/or modify it under the terms of the GNU General Public License
 as published by the Free Software Foundation; either version 2 of the
 License, or (at your option) any later version.

 This program is distributed in the hope that it will be useful, but
 WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, you can obtain a copy of the GNU
 General Public License at:
                 http://www.gnu.org/copyleft/gpl.html
 or by writing to:
           Free Software Foundation, Inc., 59 Temple Place,
                 Suite 330, Boston, MA 02111-1307 USA

 ----------------------------------------------------------------------

 Relevant literature:

 [1]  C. M. Fonseca, L. Paquete, and M. Lopez-Ibanez. An
      improved dimension-sweep algorithm for the hypervolume
      indicator. In IEEE Congress on Evolutionary Computation,
      pages 1157-1163, Vancouver, Canada, July 2006.

 [2]  Nicola Beume, Carlos M. Fonseca, Manuel López-Ibáñez, Luís
      Paquete, and J. Vahrenhold. On the complexity of computing the
      hypervolume indicator. IEEE Transactions on Evolutionary
      Computation, 13(5):1075-1082, 2009.

*************************************************************************/

#include "_hv.h"
#include <stdlib.h>
#include <stdio.h>
#include <limits.h>
#include <float.h>
#include <assert.h>

#define VARIANT 4

static int compare_tree_asc(const void *p1, const void *p2);

/*-----------------------------------------------------------------------------

  The following is a reduced version of the AVL-tree library used here
  according to the terms of the GPL. See the copyright notice below.

*/
#define AVL_DEPTH

/*****************************************************************************

    avl.h - Source code for the AVL-tree library.

    Copyright (C) 1998  Michael H. Buselli <cosine@cosine.org>
    Copyright (C) 2000-2002  Wessel Dankers <wsl@nl.linux.org>

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

    Augmented AVL-tree. Original by Michael H. Buselli <cosine@cosine.org>.

    Modified by Wessel Dankers <wsl@nl.linux.org> to add a bunch of bloat to
    the sourcecode, change the interface and squash a few bugs.
    Mail him if you find new bugs.

*****************************************************************************/

/* User supplied function to compare two items like strcmp() does.
 * For example: cmp(a,b) will return:
 *   -1  if a < b
 *    0  if a = b
 *    1  if a > b
 */
typedef int (*avl_compare_t)(const void *, const void *);

/* User supplied function to delete an item when a node is free()d.
 * If NULL, the item is not free()d.
 */
typedef void (*avl_freeitem_t)(void *);

typedef struct avl_node_t {
	struct avl_node_t *next;
	struct avl_node_t *prev;
	struct avl_node_t *parent;
	struct avl_node_t *left;
	struct avl_node_t *right;
	void *item;
	double domr;
#ifdef AVL_DEPTH
	unsigned char depth;
#endif
} avl_node_t;

typedef struct avl_tree_t {
	avl_node_t *head;
	avl_node_t *tail;
	avl_node_t *top;
	avl_compare_t cmp;
	avl_freeitem_t freeitem;
} avl_tree_t;


/*****************************************************************************

    avl.c - Source code for the AVL-tree library.

*****************************************************************************/

static void avl_rebalance(avl_tree_t *, avl_node_t *);

#ifdef AVL_DEPTH
#define NODE_DEPTH(n)  ((n) ? (n)->depth : 0)
#define L_DEPTH(n)     (NODE_DEPTH((n)->left))
#define R_DEPTH(n)     (NODE_DEPTH((n)->right))
#define CALC_DEPTH(n)  ((L_DEPTH(n)>R_DEPTH(n)?L_DEPTH(n):R_DEPTH(n)) + 1)
#endif

static int avl_check_balance(avl_node_t *avlnode) {
#ifdef AVL_DEPTH
	int d;
	d = R_DEPTH(avlnode) - L_DEPTH(avlnode);
	return d<-1?-1:d>1?1:0;
#endif
}

static int
avl_search_closest(const avl_tree_t *avltree, const void *item, avl_node_t **avlnode) {
	avl_node_t *node;
	int c;

	if(!avlnode)
		avlnode = &node;

	node = avltree->top;

	if(!node)
		return *avlnode = NULL, 0;
        

	for(;;) {
		c = compare_tree_asc(item, node->item);

		if(c < 0) {
			if(node->left)
				node = node->left;
			else
				return *avlnode = node, -1;
		} else if(c > 0) {
			if(node->right)
				node = node->right;
			else
				return *avlnode = node, 1;
		} else {
			return *avlnode = node, 0;
		}
	}
}

static avl_tree_t *
avl_init_tree(avl_tree_t *rc, avl_compare_t cmp, avl_freeitem_t freeitem) {
	if(rc) {
		rc->head = NULL;
		rc->tail = NULL;
		rc->top = NULL;
		rc->cmp = cmp;
		rc->freeitem = freeitem;
	}
	return rc;
}

static avl_tree_t *
avl_alloc_tree(avl_compare_t cmp, avl_freeitem_t freeitem) {
	return avl_init_tree(malloc(sizeof(avl_tree_t)), cmp, freeitem);
}

static void
avl_clear_tree(avl_tree_t *avltree) {
	avltree->top = avltree->head = avltree->tail = NULL;
}

static void 
avl_clear_node(avl_node_t *newnode) {
	newnode->left = newnode->right = NULL;
	#ifdef AVL_COUNT
	newnode->count = 1;
	#endif
	#ifdef AVL_DEPTH
	newnode->depth = 1;
	#endif
}

static avl_node_t *
avl_insert_top(avl_tree_t *avltree, avl_node_t *newnode) {
	avl_clear_node(newnode);
	newnode->prev = newnode->next = newnode->parent = NULL;
	avltree->head = avltree->tail = avltree->top = newnode;
	return newnode;
}

static avl_node_t *
avl_insert_before(avl_tree_t *avltree, avl_node_t *node, avl_node_t *newnode) {
/*	if(!node)
		return avltree->tail
			? avl_insert_after(avltree, avltree->tail, newnode)
			: avl_insert_top(avltree, newnode);

	if(node->left)
		return avl_insert_after(avltree, node->prev, newnode);
*/
        assert (node);
        assert (!node->left);

	avl_clear_node(newnode);

	newnode->next = node;
	newnode->parent = node;

	newnode->prev = node->prev;
	if(node->prev)
		node->prev->next = newnode;
	else
		avltree->head = newnode;
	node->prev = newnode;

	node->left = newnode;
	avl_rebalance(avltree, node);
	return newnode;
}

static avl_node_t *
avl_insert_after(avl_tree_t *avltree, avl_node_t *node, avl_node_t *newnode) {
/*	if(!node)
		return avltree->head
			? avl_insert_before(avltree, avltree->head, newnode)
			: avl_insert_top(avltree, newnode);

	if(node->right)
		return avl_insert_before(avltree, node->next, newnode);
*/
        assert (node);
        assert (!node->right);

	avl_clear_node(newnode);

	newnode->prev = node;
	newnode->parent = node;

	newnode->next = node->next;
	if(node->next)
		node->next->prev = newnode;
	else
		avltree->tail = newnode;
	node->next = newnode;

	node->right = newnode;
	avl_rebalance(avltree, node);
	return newnode;
}

/*
 * avl_unlink_node:
 * Removes the given node.  Does not delete the item at that node.
 * The item of the node may be freed before calling avl_unlink_node.
 * (In other words, it is not referenced by this function.)
 */
static void
avl_unlink_node(avl_tree_t *avltree, avl_node_t *avlnode) {
	avl_node_t *parent;
	avl_node_t **superparent;
	avl_node_t *subst, *left, *right;
	avl_node_t *balnode;

	if(avlnode->prev)
		avlnode->prev->next = avlnode->next;
	else
		avltree->head = avlnode->next;

	if(avlnode->next)
		avlnode->next->prev = avlnode->prev;
	else
		avltree->tail = avlnode->prev;

	parent = avlnode->parent;

	superparent = parent
		? avlnode == parent->left ? &parent->left : &parent->right
		: &avltree->top;

	left = avlnode->left;
	right = avlnode->right;
	if(!left) {
		*superparent = right;
		if(right)
			right->parent = parent;
		balnode = parent;
	} else if(!right) {
		*superparent = left;
		left->parent = parent;
		balnode = parent;
	} else {
		subst = avlnode->prev;
		if(subst == left) {
			balnode = subst;
		} else {
			balnode = subst->parent;
			balnode->right = subst->left;
			if(balnode->right)
				balnode->right->parent = balnode;
			subst->left = left;
			left->parent = subst;
		}
		subst->right = right;
		subst->parent = parent;
		right->parent = subst;
		*superparent = subst;
	}

	avl_rebalance(avltree, balnode);
}

/*
 * avl_rebalance:
 * Rebalances the tree if one side becomes too heavy.  This function
 * assumes that both subtrees are AVL-trees with consistant data.  The
 * function has the additional side effect of recalculating the count of
 * the tree at this node.  It should be noted that at the return of this
 * function, if a rebalance takes place, the top of this subtree is no
 * longer going to be the same node.
 */
static void
avl_rebalance(avl_tree_t *avltree, avl_node_t *avlnode) {
	avl_node_t *child;
	avl_node_t *gchild;
	avl_node_t *parent;
	avl_node_t **superparent;

	parent = avlnode;

	while(avlnode) {
		parent = avlnode->parent;

		superparent = parent
			? avlnode == parent->left ? &parent->left : &parent->right
			: &avltree->top;

		switch(avl_check_balance(avlnode)) {
		case -1:
			child = avlnode->left;
			#ifdef AVL_DEPTH
			if(L_DEPTH(child) >= R_DEPTH(child)) {
			#else
			#ifdef AVL_COUNT
			if(L_COUNT(child) >= R_COUNT(child)) {
			#else
			#error No balancing possible.
			#endif
			#endif
				avlnode->left = child->right;
				if(avlnode->left)
					avlnode->left->parent = avlnode;
				child->right = avlnode;
				avlnode->parent = child;
				*superparent = child;
				child->parent = parent;
				#ifdef AVL_COUNT
				avlnode->count = CALC_COUNT(avlnode);
				child->count = CALC_COUNT(child);
				#endif
				#ifdef AVL_DEPTH
				avlnode->depth = CALC_DEPTH(avlnode);
				child->depth = CALC_DEPTH(child);
				#endif
			} else {
				gchild = child->right;
				avlnode->left = gchild->right;
				if(avlnode->left)
					avlnode->left->parent = avlnode;
				child->right = gchild->left;
				if(child->right)
					child->right->parent = child;
				gchild->right = avlnode;
				if(gchild->right)
					gchild->right->parent = gchild;
				gchild->left = child;
				if(gchild->left)
					gchild->left->parent = gchild;
				*superparent = gchild;
				gchild->parent = parent;
				#ifdef AVL_COUNT
				avlnode->count = CALC_COUNT(avlnode);
				child->count = CALC_COUNT(child);
				gchild->count = CALC_COUNT(gchild);
				#endif
				#ifdef AVL_DEPTH
				avlnode->depth = CALC_DEPTH(avlnode);
				child->depth = CALC_DEPTH(child);
				gchild->depth = CALC_DEPTH(gchild);
				#endif
			}
		break;
		case 1:
			child = avlnode->right;
			#ifdef AVL_DEPTH
			if(R_DEPTH(child) >= L_DEPTH(child)) {
			#else
			#ifdef AVL_COUNT
			if(R_COUNT(child) >= L_COUNT(child)) {
			#else
			#error No balancing possible.
			#endif
			#endif
				avlnode->right = child->left;
				if(avlnode->right)
					avlnode->right->parent = avlnode;
				child->left = avlnode;
				avlnode->parent = child;
				*superparent = child;
				child->parent = parent;
				#ifdef AVL_COUNT
				avlnode->count = CALC_COUNT(avlnode);
				child->count = CALC_COUNT(child);
				#endif
				#ifdef AVL_DEPTH
				avlnode->depth = CALC_DEPTH(avlnode);
				child->depth = CALC_DEPTH(child);
				#endif
			} else {
				gchild = child->left;
				avlnode->right = gchild->left;
				if(avlnode->right)
					avlnode->right->parent = avlnode;
				child->left = gchild->right;
				if(child->left)
					child->left->parent = child;
				gchild->left = avlnode;
				if(gchild->left)
					gchild->left->parent = gchild;
				gchild->right = child;
				if(gchild->right)
					gchild->right->parent = gchild;
				*superparent = gchild;
				gchild->parent = parent;
				#ifdef AVL_COUNT
				avlnode->count = CALC_COUNT(avlnode);
				child->count = CALC_COUNT(child);
				gchild->count = CALC_COUNT(gchild);
				#endif
				#ifdef AVL_DEPTH
				avlnode->depth = CALC_DEPTH(avlnode);
				child->depth = CALC_DEPTH(child);
				gchild->depth = CALC_DEPTH(gchild);
				#endif
			}
		break;
		default:
			#ifdef AVL_COUNT
			avlnode->count = CALC_COUNT(avlnode);
			#endif
			#ifdef AVL_DEPTH
			avlnode->depth = CALC_DEPTH(avlnode);
			#endif
		}
		avlnode = parent;
	}
}

/*------------------------------------------------------------------------------
 end of functions from AVL-tree library.
*******************************************************************************/

#if !defined(VARIANT) || VARIANT < 1 || VARIANT > 4
#error VARIANT must be either 1, 2, 3 or 4, e.g., 'make VARIANT=4'
#endif

#if __GNUC__ >= 3
# define __hv_unused    __attribute__ ((unused))
#else
# define __hv_unused    /* no 'unused' attribute available */
#endif

#if VARIANT < 3
# define __variant3_only __hv_unused
#else
# define __variant3_only
#endif

#if VARIANT < 2
# define __variant2_only __hv_unused
#else
# define __variant2_only
#endif

typedef struct dlnode {
    double *x;                    /* The data vector              */
    struct dlnode **next;         /* Next-node vector             */
    struct dlnode **prev;         /* Previous-node vector         */
    struct avl_node_t * tnode;
    int ignore;
    int ignore_best; //used in define_order
#if VARIANT >= 2
    double *area;                 /* Area */
#endif
#if VARIANT >= 3
    double *vol;                  /* Volume */
#endif
} dlnode_t;

static avl_tree_t *tree;
#if VARIANT < 4
int stop_dimension = 1; /* default: stop on dimension 2 */
#else
int stop_dimension = 2; /* default: stop on dimension 3 */
#endif

static int compare_node(const void *p1, const void* p2)
{
    const double x1 = *((*(const dlnode_t **)p1)->x);
    const double x2 = *((*(const dlnode_t **)p2)->x);

    return (x1 < x2) ? -1 : (x1 > x2) ? 1 : 0;
}

static int compare_tree_asc(const void *p1, const void *p2)
{
    const double *x1 = (const double *)p1;
    const double *x2 = (const double *)p2;

    return (x1[1] > x2[1]) ? -1 : (x1[1] < x2[1]) ? 1
        : (x1[0] >= x2[0]) ? -1 : 1;
}

/*
 * Setup circular double-linked list in each dimension
 */

static dlnode_t *
setup_cdllist(double *data, int d, int n)
{
    dlnode_t *head;
    dlnode_t **scratch;
    int i, j;

    head  = malloc ((n+1) * sizeof(dlnode_t));

    head->x = data;
    head->ignore = 0;  /* should never get used */
    head->next = malloc( d * (n+1) * sizeof(dlnode_t*));
    head->prev = malloc( d * (n+1) * sizeof(dlnode_t*));
    head->tnode = malloc ((n+1) * sizeof(avl_node_t));

#if VARIANT >= 2
    head->area = malloc(d * (n+1) * sizeof(double));
#endif
#if VARIANT >= 3
    head->vol = malloc(d * (n+1) * sizeof(double));
#endif

    for (i = 1; i <= n; i++) {
        head[i].x = head[i-1].x + d;/* this will be fixed a few lines below... */
        head[i].ignore = 0;
        head[i].next = head[i-1].next + d;
        head[i].prev = head[i-1].prev + d;
        head[i].tnode = head[i-1].tnode + 1;
#if VARIANT >= 2
        head[i].area = head[i-1].area + d;
#endif
#if VARIANT >= 3
        head[i].vol = head[i-1].vol + d;
#endif
    }
    head->x = NULL; /* head contains no data */

    scratch = malloc(n * sizeof(dlnode_t*));
    for (i = 0; i < n; i++)
        scratch[i] = head + i + 1;

    for (j = d-1; j >= 0; j--) {
        for (i = 0; i < n; i++)
            scratch[i]->x--;
        qsort(scratch, n, sizeof(dlnode_t*), compare_node);
        head->next[j] = scratch[0];
        scratch[0]->prev[j] = head;
        for (i = 1; i < n; i++) {
            scratch[i-1]->next[j] = scratch[i];
            scratch[i]->prev[j] = scratch[i-1];
        }
        scratch[n-1]->next[j] = head;
        head->prev[j] = scratch[n-1];
    }
    
    free(scratch);

    for (i = 1; i <= n; i++) {
        (head[i].tnode)->item = head[i].x;
    }

    return head;
}

static void free_cdllist(dlnode_t * head)
{
    free(head->tnode); /* Frees _all_ nodes. */
    free(head->next);
    free(head->prev);
#if VARIANT >= 2
    free(head->area);
#endif
#if VARIANT >= 3
    free(head->vol);
#endif
    free(head);
}

static void delete (dlnode_t *nodep, int dim, double * bound __variant3_only)
{
    int i;

    for (i = stop_dimension; i < dim; i++) {
        nodep->prev[i]->next[i] = nodep->next[i];
        nodep->next[i]->prev[i] = nodep->prev[i];
#if VARIANT >= 3
        if (bound[i] > nodep->x[i])
            bound[i] = nodep->x[i];
#endif
  }
}

#if VARIANT >= 2
static void delete_dom (dlnode_t *nodep, int dim)
{
    int i;

    for (i = stop_dimension; i < dim; i++) {
        nodep->prev[i]->next[i] = nodep->next[i];
        nodep->next[i]->prev[i] = nodep->prev[i];
    }
}
#endif

static void reinsert (dlnode_t *nodep, int dim, double * bound __variant3_only)
{
    int i;

    for (i = stop_dimension; i < dim; i++) {
        nodep->prev[i]->next[i] = nodep;
        nodep->next[i]->prev[i] = nodep;
#if VARIANT >= 3
        if (bound[i] > nodep->x[i])
            bound[i] = nodep->x[i];
#endif
    }
}

#if VARIANT >= 2
static void reinsert_dom (dlnode_t *nodep, int dim)
{
    int i;
    for (i = stop_dimension; i < dim; i++) {
        dlnode_t *p = nodep->prev[i];
        p->next[i] = nodep;
        nodep->next[i]->prev[i] = nodep;
        nodep->area[i] = p->area[i];

    #if VARIANT >= 3
        nodep->vol[i] = p->vol[i] + p->area[i] * (nodep->x[i] - p->x[i]);
    #endif
    }
}
#endif

static double
hv_recursive(dlnode_t *list, int dim, int c, const double * ref,
             double * bound)
{   
    /* ------------------------------------------------------
       General case for dimensions higher than stop_dimension
       ------------------------------------------------------ */
    if ( dim > stop_dimension ) {
        dlnode_t *p0 = list;
        dlnode_t *p1 = list->prev[dim];
        double hyperv = 0;
#if VARIANT == 1
        double hypera;
#endif
#if VARIANT >= 2
        dlnode_t *pp;
        for (pp = p1; pp->x; pp = pp->prev[dim]) {
            if (pp->ignore < dim)
                pp->ignore = 0;
        }
#endif
        while (c > 1
#if VARIANT >= 3
               /* We delete all points x[dim] > bound[dim]. In case of
                  repeated coordinates, we also delete all points
                  x[dim] == bound[dim] except one. */
               && (p1->x[dim] > bound[dim] 
                   || p1->prev[dim]->x[dim] >= bound[dim])
#endif
            ) {
            p0 = p1;
#if VARIANT >=2
            if (p0->ignore >= dim)
                delete_dom(p0, dim);
            else
                delete(p0, dim, bound);
#else
            delete(p0, dim, bound);
#endif
            p1 = p0->prev[dim];
            c--;
        }

#if VARIANT == 1
        hypera = hv_recursive(list, dim-1, c, ref, bound);

#elif VARIANT == 2
        int i;
        p1->area[0] = 1;
        for (i = 1; i <= dim; i++)
            p1->area[i] = p1->area[i-1] * (ref[i-1] - p1->x[i-1]);
        
#elif VARIANT >= 3
        if (c > 1) {
            hyperv = p1->prev[dim]->vol[dim] + p1->prev[dim]->area[dim]
                * (p1->x[dim] - p1->prev[dim]->x[dim]);
            
            if (p1->ignore >= dim)
                p1->area[dim] = p1->prev[dim]->area[dim];
            else {
                p1->area[dim] = hv_recursive(list, dim - 1, c, ref, bound);
                /* At this point, p1 is the point with the highest value in
                   dimension dim in the list, so if it is dominated in
                   dimension dim-1, so it is also dominated in dimension
                   dim. */
                if (p1->ignore == (dim - 1))
                    p1->ignore = dim; 
            }
        } else {
            int i;
            p1->area[0] = 1;
            for (i = 1; i <= dim; i++)
                p1->area[i] = p1->area[i-1] * (ref[i-1] - p1->x[i-1]);
        }
        p1->vol[dim] = hyperv;
#endif

        while (p0->x != NULL) {

#if VARIANT == 1
            hyperv += hypera * (p0->x[dim] - p1->x[dim]);
#else
            hyperv += p1->area[dim] * (p0->x[dim] - p1->x[dim]);
#endif
            c++;
#if VARIANT >= 2
            if (p0->ignore >= dim) {
                reinsert_dom (p0, dim);
                p0->area[dim] = p1->area[dim];
            } else {
#endif
                reinsert (p0, dim, bound);
#if VARIANT >= 2
                p0->area[dim] = hv_recursive (list, dim-1, c, ref, bound);
                if (p0->ignore == (dim - 1))
                    p0->ignore = dim;
            }
#elif VARIANT == 1
            hypera = hv_recursive (list, dim-1, c, ref, NULL);
#endif
            p1 = p0;
            p0 = p0->next[dim];
#if VARIANT >= 3
            p1->vol[dim] = hyperv;
#endif
        }
#if VARIANT >= 3
        bound[dim] = p1->x[dim];
#endif

#if VARIANT == 1
        hyperv += hypera * (ref[dim] - p1->x[dim]);
#else
        hyperv += p1->area[dim] * (ref[dim] - p1->x[dim]);
#endif
        return hyperv;
    }


    /* ---------------------------
       special case of dimension 3
       --------------------------- */
    else if (dim == 2) {
        double hyperv;
        double hypera;
        double height;
        
#if VARIANT >= 3
        dlnode_t *pp = list->prev[2];
        avl_node_t *tnode;

        /* All the point that have value of x[2] lower than bound[2] are points
           that were previously processed, so there's no need to process them
           again.  In this case, every point was processed before, so the
           volume is known.  */
        if (pp->x[2] < bound[2])
            return pp->vol[2] + pp->area[2] * (ref[2] - pp->x[2]);

        pp = list->next[2];

        /* In this case, every point has to be processed.  */
        if (pp->x[2] >= bound[2]) {
            pp->tnode->domr = ref[2];
            pp->area[2] = (ref[0] - pp->x[0]) * (ref[1] - pp->x[1]);
            pp->vol[2] = 0;
            pp->ignore = 0;
        } else {
            /* Otherwise, we look for the first point that has to be in the
               tree, by searching for the first point that isn't dominated or
               that is dominated by a point with value of x[2] higher or equal
               than bound[2] (domr keeps the value of the x[2] of the point
               that dominates pp, or ref[2] if it isn't dominated).  */
            while (pp->tnode->domr < bound[2]) {
                pp = pp->next[2];
            }
        }

        pp->ignore = 0;
        avl_insert_top(tree,pp->tnode);
        pp->tnode->domr = ref[2];
        
        /* Connect all points that aren't dominated or that are dominated and
           the point that dominates it has value x[2] (pp->tnode->domr) equal
           or higher than bound[2].  */
        for (pp = pp->next[2]; pp->x[2] < bound[2]; pp = pp->next[2]) {
            if (pp->tnode->domr >= bound[2]) {
                avl_node_t *tnodeaux = pp->tnode;
                tnodeaux->domr = ref[2];
                if (avl_search_closest(tree, pp->x, &tnode) <= 0)
                    avl_insert_before(tree, tnode, tnodeaux);
                else
                    avl_insert_after(tree, tnode, tnodeaux);
            }
        }
        pp = pp->prev[2];
        hyperv = pp->vol[2];    
        hypera = pp->area[2];

        height = (pp->next[2]->x) 
            ? pp->next[2]->x[2] - pp->x[2]
            : ref[2] - pp->x[2];

        bound[2] = list->prev[2]->x[2];
#else 
/* VARIANT <= 2 */
        dlnode_t *pp = list->next[2];
        hyperv = 0;

        hypera = (ref[0] - pp->x[0])*(ref[1] - pp->x[1]);
        height = (c == 1) 
            ? ref[2] - pp->x[2]
            : pp->next[2]->x[2] - pp->x[2];

        avl_insert_top(tree,pp->tnode);
#endif
        hyperv += hypera * height;
        for (pp = pp->next[2]; pp->x != NULL; pp = pp->next[2]) {
            const double * prv_ip, * nxt_ip;
            avl_node_t *tnode;
            int cmp;

#if VARIANT >= 3
            pp->vol[2] = hyperv;
#endif  
            height = (pp == list->prev[2])
                ? ref[2] - pp->x[2]
                : pp->next[2]->x[2] - pp->x[2];
#if VARIANT >= 2
            if (pp->ignore >= 2) {
                hyperv += hypera * height;
#if VARIANT >= 3
                pp->area[2] = hypera;
#endif
                continue;
            } 
#endif
            cmp = avl_search_closest(tree, pp->x, &tnode);
            if (cmp <= 0) {
                nxt_ip = (double *)(tnode->item);
            } else {
                nxt_ip = (tnode->next != NULL)
                    ? (double *)(tnode->next->item)
                    : ref;
            }
            if (nxt_ip[0] <= pp->x[0]) {
                pp->ignore = 2;
#if VARIANT >= 3
                pp->tnode->domr = pp->x[2];
                pp->area[2] = hypera;
#endif
                if (height > 0)
                    hyperv += hypera * height;
                continue;
            }
            if (cmp <= 0) {
                avl_insert_before(tree, tnode, pp->tnode);
                tnode = pp->tnode->prev;
            } else {
                avl_insert_after(tree, tnode, pp->tnode);
            }
#if VARIANT >= 3
            pp->tnode->domr = ref[2];
#endif
            if (tnode != NULL) {
                prv_ip = (double *)(tnode->item);
                if (prv_ip[0] >= pp->x[0]) {
                    const double * cur_ip;
                    
                    tnode = pp->tnode->prev;
                    /* cur_ip = point dominated by pp with highest
                       [0]-coordinate.  */
                    cur_ip = (double *)(tnode->item);
                    while (tnode->prev) {
                        prv_ip = (double *)(tnode->prev->item);
                        hypera -= (prv_ip[1] - cur_ip[1]) * (nxt_ip[0] - cur_ip[0]);
                        if (prv_ip[0] < pp->x[0])
                            break; /* prv is not dominated by pp */
                        cur_ip = prv_ip;
                        avl_unlink_node(tree,tnode);
#if VARIANT >= 3
                        /* saves the value of x[2] of the point that
                           dominates tnode. */
                        tnode->domr = pp->x[2];
#endif
                        tnode = tnode->prev;
                    }
                    
                    avl_unlink_node(tree, tnode);
#if VARIANT >= 3
                    tnode->domr = pp->x[2];
#endif
                    if (!tnode->prev) {
                        hypera -= (ref[1] - cur_ip[1]) * (nxt_ip[0] - cur_ip[0]);
                        prv_ip = ref;
                    }
                }
            } else
                prv_ip = ref;
            
            hypera += (prv_ip[1] - pp->x[1]) * (nxt_ip[0] - pp->x[0]);
            
            if (height > 0)
                hyperv += hypera * height;
#if VARIANT >= 3
            pp->area[2] = hypera;
#endif
        }
        avl_clear_tree(tree);
        return hyperv;
    }

    /* special case of dimension 2 */
    else if (dim == 1) {
        const dlnode_t *p1 = list->next[1]; 
        double hypera = p1->x[0];
        double hyperv = 0;
        dlnode_t *p0;

        while ((p0 = p1->next[1])->x) {
            hyperv += (ref[0] - hypera) * (p0->x[1] - p1->x[1]);
            if (p0->x[0] < hypera)
                hypera = p0->x[0];
            else if (p0->ignore == 0)
                p0->ignore = 1;
            p1 = p0;
        }
        hyperv += (ref[0] - hypera) * (ref[1] - p1->x[1]);
        return hyperv;
    }

    /* special case of dimension 1 */
    else if (dim == 0) {
        list->next[0]->ignore = -1;
        return (ref[0] - list->next[0]->x[0]);
    } 
    else {
        fprintf(stderr, "%s:%d: unreachable condition! \n"
                "This is a bug, please report it to "
                "manuel.lopez-ibanez@ulb.ac.be\n", __FILE__, __LINE__);
        exit(EXIT_FAILURE);
    }
}

/*
  Removes the point from the circular double-linked list, but it
  doesn't remove the data.
*/
static void
filter_delete_node(dlnode_t *node, int d)
{
    int i;

    for (i = 0; i < d; i++) {
        node->next[i]->prev[i] = node->prev[i];
        node->prev[i]->next[i] = node->next[i];
    }
}

/*
  Filters those points that do not strictly dominate the reference
  point.  This is needed to assure that the points left are only those
  that are needed to calculate the hypervolume.
*/
static int
filter(dlnode_t *list, int d, int n, const double *ref)
{
    int i, j;
    
    /* fprintf (stderr, "%d points initially\n", n); */
    for (i = 0; i < d; i++) {
        dlnode_t *aux = list->prev[i];
        int np = n;
        for (j = 0; j < np; j++) {
            if (aux->x[i] < ref[i])
                break;
            filter_delete_node (aux, d);
            aux = aux->prev[i];
            n--;
        }
    }
    /* fprintf (stderr, "%d points remain\n", n); */
    return n;
}

double fpli_hv(double *data, int d, int n, const double *ref)
{
    dlnode_t *list;
    double hyperv;
    double * bound = NULL;

#if VARIANT >= 3
    int i;

    bound = malloc (d * sizeof(double));
    for (i = 0; i < d; i++) bound[i] = -DBL_MAX;
#endif

    tree  = avl_alloc_tree ((avl_compare_t) compare_tree_asc,
                            (avl_freeitem_t) NULL);

    list = setup_cdllist(data, d, n);

    n = filter(list, d, n, ref);
    if (n == 0) { 
        hyperv = 0.0;
    } else if (n == 1) {
        dlnode_t * p = list->next[0];
        hyperv = 1;
        for (i = 0; i < d; i++)
            hyperv *= ref[i] - p->x[i];
    } else {
        hyperv = hv_recursive(list, d-1, n, ref, bound);
    }
    /* Clean up.  */
    free_cdllist (list);
    free (tree);  /* The nodes are freed by free_cdllist ().  */
    free (bound); 

    return hyperv;
}
